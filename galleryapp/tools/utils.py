import random
import string
from django.core.mail import send_mail
from django.conf import settings


def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices(string.digits, k=6))


def send_verification_email(email, code):
    """发送验证码邮件"""
    subject = '邮箱验证码 - SuGallery'
    message = f'''
    您好！

    您的验证码是：{code}

    该验证码在10分钟内有效，请尽快完成验证。
    如果这不是您的操作，请忽略此邮件。

    此致
    SuGallery 团队
    '''
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Send email error: {e}")
        return False
