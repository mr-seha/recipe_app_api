from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
UserManager
)
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('ایمیل کاربر نمیتواند خالی باشد!')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_super_user(self, email, password=None, **extra_fields):
        return self.create_user(email, password, is_superuser=True, is_staff=True, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255, verbose_name='ایمیل')
    name = models.CharField(max_length=255, verbose_name='نام')
    is_active = models.BooleanField(default=True, verbose_name='کاربر فعال؟')
    is_staff = models.BooleanField(default=False, verbose_name='کاربر مدیر؟')

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربر"
