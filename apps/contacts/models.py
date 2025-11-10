from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class Tag(OrganizationScopedModel):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=32, blank=True)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ("name",)

    def __str__(self):
        return self.name


class Contact(OrganizationScopedModel, UserTrackedModel):
    class Stage(models.TextChoices):
        LEAD = "lead", "Lead"
        PROSPECT = "prospect", "Prospect"
        CUSTOMER = "customer", "Customer"
        INACTIVE = "inactive", "Inactive"

    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        REFERRAL = "referral", "Referral"
        COLD_CALL = "cold_call", "Cold Call"
        IMPORT = "import", "Import"
        API = "api", "API"

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    mobile = models.CharField(max_length=32, blank=True)
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
    )
    job_title = models.CharField(max_length=150, blank=True)
    stage = models.CharField(max_length=32, choices=Stage.choices, default=Stage.LEAD)
    source = models.CharField(max_length=32, choices=Source.choices, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_contacts",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="contacts")
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=("organization", "created_at")),
            models.Index(fields=("organization", "owner")),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()
