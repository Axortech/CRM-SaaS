from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class Task(OrganizationScopedModel, UserTrackedModel):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    opportunity = models.ForeignKey(
        "opportunities.Opportunity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=255, blank=True)
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_tasks",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("organization", "assigned_to")),
            models.Index(fields=("organization", "due_date")),
        ]

    def __str__(self):
        return self.title
