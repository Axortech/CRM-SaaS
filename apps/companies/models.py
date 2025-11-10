from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class Company(OrganizationScopedModel, UserTrackedModel):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=150, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=150, blank=True)
    state = models.CharField(max_length=150, blank=True)
    country = models.CharField(max_length=150, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    parent_company = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subsidiaries",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_companies",
    )
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=("organization", "owner")),
        ]

    def __str__(self):
        return self.name
