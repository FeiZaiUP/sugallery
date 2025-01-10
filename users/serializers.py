from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings
from .models import EmailVerification


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()  # 重写avatar字段，调用自定义方法

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'store_name', 'user_type', 'first_name', 'last_name', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return request.build_absolute_uri("/media/default/avatar.png") if request else "/media/default/avatar.png"


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    email_verification_code = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'password2', 'email_verification_code']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_username(self, value):
        if get_user_model().objects.filter(username=value).exists():
            raise serializers.ValidationError("该用户名已被使用")
        return value

    def validate_email(self, value):
        if get_user_model().objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("密码长度不能少于8个字符")
        return value

    def validate(self, data):
        # 验证密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "两次输入的密码不匹配"})

        # 验证邮箱验证码
        try:
            verification = EmailVerification.objects.get(
                email=data['email'],
                code=data['email_verification_code'],
                is_verified=False
            )
            if verification.is_expired:
                raise serializers.ValidationError({"email": "验证码已过期，请重新获取"})
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError({"email": "验证码错误或邮箱未验证"})

        return data

    def create(self, validated_data):

        # 移除不需要的字段
        validated_data.pop('password2', None)
        validated_data.pop('email_verification_code', None)
        # 创建用户
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user