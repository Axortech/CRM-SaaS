from django.db import models
from django.utils import timezone

from core.models import OrganizationScopedModel, UUIDModel, TimeStampedModel


class Subscription(OrganizationScopedModel):
    class Plan(models.TextChoices):
        STARTER = "starter", "Starter"
        PROFESSIONAL = "professional", "Professional"
        ENTERPRISE = "enterprise", "Enterprise"

    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past Due"
        CANCELED = "canceled", "Canceled"
        TRIALING = "trialing", "Trialing"

    plan = models.CharField(max_length=32, choices=Plan.choices)
    billing_cycle = models.CharField(max_length=16, choices=BillingCycle.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.TRIALING)
    trial_end_date = models.DateField(null=True, blank=True)
    current_period_start = models.DateField(null=True, blank=True)
    current_period_end = models.DateField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    user_limit = models.PositiveIntegerField(default=5)

    class Meta:
        ordering = ("organization",)

    def __str__(self):
        return f"{self.organization.name} - {self.plan}"


class Payment(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    invoice_number = models.CharField(max_length=64, blank=True)
    invoice_pdf_url = models.URLField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def mark_paid(self):
        self.status = self.Status.SUCCEEDED
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at", "updated_at"])

    def __str__(self):
        return f"{self.invoice_number or self.id} - {self.status}"


class PaymentMethod(UUIDModel, TimeStampedModel):
    class MethodType(models.TextChoices):
        CARD = "card", "Card"
        BANK = "bank", "Bank"

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="payment_methods",
    )
    method_type = models.CharField(max_length=16, choices=MethodType.choices, default=MethodType.CARD)
    brand = models.CharField(max_length=32, blank=True)
    last4 = models.CharField(max_length=4, blank=True)
    exp_month = models.PositiveIntegerField(null=True, blank=True)
    exp_year = models.PositiveIntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    external_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.brand} •••• {self.last4}"
