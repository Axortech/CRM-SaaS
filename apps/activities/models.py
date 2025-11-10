from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class Activity(OrganizationScopedModel, UserTrackedModel):
    class ActivityType(models.TextChoices):
        CALL = "call", "Call"
        EMAIL = "email", "Email"
        MEETING = "meeting", "Meeting"
        NOTE = "note", "Note"

    activity_type = models.CharField(max_length=32, choices=ActivityType.choices)
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)
    occurred_at = models.DateTimeField()
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    opportunity = models.ForeignKey(
        "opportunities.Opportunity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [
            models.Index(fields=("organization", "occurred_at")),
            models.Index(fields=("organization", "activity_type")),
        ]

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.subject}"
