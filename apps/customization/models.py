from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class CustomField(OrganizationScopedModel, UserTrackedModel):
    class EntityType(models.TextChoices):
        CONTACT = "contact", "Contact"
        COMPANY = "company", "Company"
        OPPORTUNITY = "opportunity", "Opportunity"
        TASK = "task", "Task"

    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        DATE = "date", "Date"
        DROPDOWN = "dropdown", "Dropdown"
        CHECKBOX = "checkbox", "Checkbox"
        TEXTAREA = "textarea", "Textarea"

    entity_type = models.CharField(max_length=32, choices=EntityType.choices)
    field_name = models.CharField(max_length=100)
    field_label = models.CharField(max_length=150)
    field_type = models.CharField(max_length=32, choices=FieldType.choices)
    options = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "entity_type", "field_name")
        ordering = ("entity_type", "order")

    def __str__(self):
        return f"{self.field_label} ({self.entity_type})"


class LayoutConfiguration(OrganizationScopedModel, UserTrackedModel):
    class PageType(models.TextChoices):
        DASHBOARD = "dashboard", "Dashboard"
        CONTACT_LIST = "contact_list", "Contact List"
        CONTACT_DETAIL = "contact_detail", "Contact Detail"
        COMPANY_DETAIL = "company_detail", "Company Detail"
        OPPORTUNITY_PIPELINE = "opportunity_pipeline", "Opportunity Pipeline"
        TASKS = "tasks", "Tasks"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="layout_configurations",
    )
    page_type = models.CharField(max_length=64, choices=PageType.choices)
    configuration = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("organization", "user", "page_type", "is_default")

    def __str__(self):
        return f"{self.page_type} layout"
