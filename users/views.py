# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView
from .serializers import RegisterSerializer, UserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.cache import cache  # 导入 cache
from django.core.mail import send_mail
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from galleryapp.tools.captcha import CaptchaUtil
from galleryapp.tools.utils import generate_verification_code, send_verification_email
from .serializers import RegisterSerializer, EmailVerificationSerializer, VerifyEmailSerializer
from .models import EmailVerification
import uuid
import logging
import random

logger = logging.getLogger(__name__)


class SendVerificationCodeView(APIView):
    """发送邮箱验证码"""

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = EmailVerificationSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            # 检查邮箱是否已被注册
            if get_user_model().objects.filter(email=email).exists():
                return Response(
                    {"error": "该邮箱已被注册"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # 先检查是否存在验证码记录
                try:

                    verification = EmailVerification.objects.get(email=email)

                    # 检查发送频率

                    time_diff = timezone.now() - verification.created_at

                    if time_diff.seconds < settings.VERIFICATION_CODE_RESEND_INTERVAL:
                        return Response(

                            {
                                "error": f"请等待 {settings.VERIFICATION_CODE_RESEND_INTERVAL - time_diff.seconds} 秒后再试"},

                            status=status.HTTP_400_BAD_REQUEST

                        )

                except EmailVerification.DoesNotExist:

                    verification = None

                    # 生成新验证码

                    code = generate_verification_code()
                    logger.info(f"Generated verification code for {email}")

                    # 发送邮件

                    if not send_verification_email(email, code):
                        logger.error(f"Failed to send verification email to {email}")
                        return Response(

                            {"error": "发送验证码失败，请稍后重试"},

                            status=status.HTTP_500_INTERNAL_SERVER_ERROR

                        )

                    logger.info(f"Successfully sent verification email to {email}")
                    # 邮件发送成功后再保存验证码

                    if verification:

                        verification.code = code

                        verification.is_verified = False

                        verification.expires_at = timezone.now() + timedelta(

                            minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES

                        )

                        verification.save()

                    else:

                        EmailVerification.objects.create(

                            email=email,

                            code=code,

                            is_verified=False,

                            expires_at=timezone.now() + timedelta(

                                minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES

                            )

                        )

                return Response(
                    {"message": "验证码已发送到您的邮箱"},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                print(f"Error sending verification code: {str(e)}")
                return Response(
                    {"error": "发送验证码失败，请稍后重试"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    """用户注册"""

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        try:

            if serializer.is_valid():

                # 创建用户

                user = serializer.save()

                # 标记验证码已使用

                try:

                    verification = EmailVerification.objects.get(

                        email=user.email,

                        is_verified=False

                    )

                    verification.is_verified = True

                    verification.save()

                except EmailVerification.DoesNotExist:

                    pass

                return Response({
                    "message": "注册成功",
                    "user_id": user.id},
                    status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:

            print(f"Registration error: {str(e)}")

            return Response(
                {"error": "注册失败，请稍后重试"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# login
#     pass
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]  # 允许匿名用户访问此视图

    def post(self, request, *args, **kwargs):

        # # 添加测试模式
        # if settings.DEBUG and 'test_mode' in request.data:
        #     # 跳过验证码验证
        #     return super().post(request, *args, **kwargs)

        captcha_key = request.data.get('captcha_key')
        captcha_value = request.data.get('captcha')

        if not captcha_key or not captcha_value:
            return Response({'detail': 'Captcha key and value are required'}, status=status.HTTP_400_BAD_REQUEST)

        # 从缓存中获取验证码
        stored_captcha = cache.get(captcha_key)

        if not stored_captcha:
            return Response({'detail': 'Captcha has expired or does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        if not CaptchaUtil.verify_code(captcha_value, stored_captcha):
            return Response({'detail': 'Invalid captcha'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证码验证通过后，删除验证码缓存，防止重复使用
        cache.delete(captcha_key)

        # 调用父类的方法执行登录逻辑
        response = super().post(request, *args, **kwargs)

        # 可选择在这里进一步处理返回的 JWT token 信息
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 获取请求头中的 token
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

                # 将 token 加入黑名单
                RefreshToken(token).blacklist()

                # 清除用户相关的缓存
                user_cache_key = f'user_profile_{request.user.id}'
                cache.delete(user_cache_key)

                return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
            return Response({'detail': 'No token provided.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CaptchaView(APIView):
    permission_classes = [AllowAny]  # 允许匿名用户访问

    def get(self, request, *args, **kwargs):
        captcha_util = CaptchaUtil()
        code, img_str = captcha_util.generate_captcha()
        captcha_key = str(uuid.uuid4())

        # 日志记录生成的验证码
        logger.debug(f"Generated captcha: {code}")

        cache.set(captcha_key, code, timeout=300)
        logger.debug(f"Captcha stored in cache: {captcha_key} -> {code}")

        return Response({
            'captcha_key': captcha_key,
            'captcha_image': f'data:image/png;base64,{img_str}'
        }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # 只允许认证用户访问
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        user = request.user
        avatar_url = user.avatar.url if user.avatar else getattr(settings, 'DEFAULT_AVATAR_URL',
                                                                 '/media/default/avatar.png')
        return Response({
            'username': user.username,
            'email': user.email,
            'store_name': user.store_name,
            'user_type': user.user_type,
            'avatar': request.build_absolute_uri(avatar_url),
        })

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)

        avatar = request.FILES.get('avatar')

        if avatar:
            allowed_types = ['image/jpeg', 'image/png']
            # 关键：避免 avatar 为空字符串时报错
            if hasattr(avatar, 'content_type') and avatar.content_type not in allowed_types:
                return Response({'error': '仅支持 JPG 和 PNG 格式'}, status=status.HTTP_400_BAD_REQUEST)

            user.avatar = avatar
            user.save()

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
