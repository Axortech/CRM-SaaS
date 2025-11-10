from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel, TimeStampedModel


class Report(OrganizationScopedModel, UserTrackedModel):
    class ReportType(models.TextChoices):
        SALES = "sales", "Sales"
        ACTIVITY = "activity", "Activity"
        PIPELINE = "pipeline", "Pipeline"
        FORECAST = "forecast", "Forecast"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=32, choices=ReportType.choices)
    configuration = models.JSONField(default=dict)
    is_shared = models.BooleanField(default=False)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class ScheduledReport(OrganizationScopedModel):
    class Schedule(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    schedule = models.CharField(max_length=32, choices=Schedule.choices)
    recipients = models.JSONField(default=list)
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.report.name} ({self.schedule})"
