from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from .views import SendVerificationCodeView, RegisterView, UserProfileView, CaptchaView, CustomTokenObtainPairView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('send-verification-code/', SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # 获取验证码
    path('captcha/', CaptchaView.as_view(), name='captcha'),

    # 自定义 JWT 登录路由，包含验证码验证
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]
