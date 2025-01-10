from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    store_name = models.CharField(max_length=255, blank=True, null=True)  # 商铺名称
    user_type = models.CharField(max_length=50, choices=[('business', 'Business'), ('admin', 'Admin')],
                                 default='business')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # 其他扩展字段可以根据需求添加

    def __str__(self):
        return self.username


class EmailVerification(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)  # 6位验证码
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.email} - {self.code}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # 10分钟有效期
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
