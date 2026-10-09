from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email can not be empty!'))
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        return self.create_user(email, password, is_superuser=True, is_staff=True, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255, verbose_name='ایمیل')
    name = models.CharField(max_length=255, verbose_name='نام')
    is_active = models.BooleanField(default=True, verbose_name=_('is active?'))
    is_staff = models.BooleanField(default=False, verbose_name=_('is staff?'))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('user')


class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name=_('name'))

    def __str__(self):
        return self.name


class Recipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    time_minutes = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('Tag')

    def __str__(self):
        return self.title
