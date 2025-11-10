import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel, UUIDModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must provide an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    avatar_url = models.URLField(blank=True)
    email_verified = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


def generate_secure_token():
    return secrets.token_urlsafe(48)


def email_token_expiry():
    return timezone.now() + timedelta(days=2)


def password_reset_expiry():
    return timezone.now() + timedelta(days=1)


class EmailVerificationToken(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token = models.CharField(max_length=128, unique=True, default=generate_secure_token)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(default=email_token_expiry)

    class Meta:
        ordering = ("-created_at",)

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used", "updated_at"])

    def __str__(self):
        return f"EmailVerificationToken({self.user.email})"


class PasswordResetToken(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=128, unique=True, default=generate_secure_token)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(default=password_reset_expiry)

    class Meta:
        ordering = ("-created_at",)

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=["is_used", "updated_at"])

    def __str__(self):
        return f"PasswordResetToken({self.user.email})"
