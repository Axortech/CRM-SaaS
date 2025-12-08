import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

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


class Team(OrganizationScopedModel):
    """Team model for grouping organization members"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=32, blank=True, default="#1677ff")
    leader = models.ForeignKey(
        OrganizationMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams",
    )
    members = models.ManyToManyField(
        OrganizationMember,
        related_name="teams",
        blank=True,
    )

    class Meta:
        unique_together = ("organization", "name")
        ordering = ("name",)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    @property
    def member_count(self):
        """Get the number of members in the team"""
        return self.members.count()


class Invitation(OrganizationScopedModel):
    """Invitation model for inviting users to join organizations"""
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    email = models.EmailField()
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations",
    )
    teams = models.ManyToManyField(
        Team,
        related_name="invitations",
        blank=True,
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    invited_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(blank=True)

    class Meta:
        unique_together = ("organization", "email", "status")
        ordering = ("-invited_at",)
        indexes = [
            models.Index(fields=("token",)),
            models.Index(fields=("organization", "status")),
        ]

    def __str__(self):
        return f"Invitation to {self.email} for {self.organization.name}"

    def is_expired(self):
        """Check if invitation has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def mark_accepted(self):
        """Mark invitation as accepted"""
        from django.utils import timezone
        self.status = self.Status.ACCEPTED
        self.accepted_at = timezone.now()
        self.save(update_fields=["status", "accepted_at"])

    def cancel(self):
        """Cancel the invitation"""
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])