from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel


class Notification(OrganizationScopedModel):
    class NotificationType(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Task Assigned"
        OPPORTUNITY_WON = "opportunity_won", "Opportunity Won"
        PAYMENT_FAILED = "payment_failed", "Payment Failed"
        GENERIC = "generic", "Generic"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=64, choices=NotificationType.choices, default=NotificationType.GENERIC)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("organization", "user")),
            models.Index(fields=("organization", "is_read")),
        ]

    def __str__(self):
        return self.title


class AuditLogEntry(OrganizationScopedModel):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        VIEW = "view", "View"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=16, choices=Action.choices)
    entity_type = models.CharField(max_length=150)
    entity_id = models.CharField(max_length=64)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)
        indexes = [
            models.Index(fields=("organization", "entity_type")),
            models.Index(fields=("organization", "timestamp")),
        ]

    def __str__(self):
        return f"{self.action} {self.entity_type}"
