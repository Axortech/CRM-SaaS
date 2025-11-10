from django.conf import settings
from django.db import models

from core.models import TimeStampedModel, UUIDModel, OrganizationScopedModel


class Organization(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    subdomain = models.CharField(max_length=64, unique=True, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_organizations",
    )
    is_active = models.BooleanField(default=True)
    timezone = models.CharField(max_length=64, default="UTC")
    business_hours = models.JSONField(default=dict, blank=True)
    logo_url = models.URLField(blank=True)
    favicon_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=32, blank=True)
    secondary_color = models.CharField(max_length=32, blank=True)
    custom_domain = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Role(OrganizationScopedModel):
    name = models.CharField(max_length=150)
    is_system_role = models.BooleanField(default=False)
    permissions = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ("organization", "name")

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class OrganizationMember(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    invitation_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ("organization", "user")
        ordering = ("organization", "user")

    def __str__(self):
        return f"{self.user.email} @ {self.organization.name}"
