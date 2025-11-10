from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class OpportunityStage(OrganizationScopedModel):
    name = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=0)
    probability = models.PositiveIntegerField(default=0)
    is_closed_stage = models.BooleanField(default=False)
    is_won_stage = models.BooleanField(default=False)
    color = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ("organization", "order")
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class Opportunity(OrganizationScopedModel, UserTrackedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    name = models.CharField(max_length=255)
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunities",
    )
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunities",
    )
    stage = models.ForeignKey(
        OpportunityStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunities",
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default="USD")
    probability = models.PositiveIntegerField(default=0)
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    loss_reason = models.TextField(blank=True)
    source = models.CharField(max_length=64, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_opportunities",
    )
    custom_fields = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=("organization", "stage")),
            models.Index(fields=("organization", "status")),
            models.Index(fields=("organization", "owner")),
        ]

    def __str__(self):
        return self.name


class OpportunityLineItem(models.Model):
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product_name} ({self.opportunity.name})"
