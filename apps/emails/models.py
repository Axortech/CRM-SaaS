from django.conf import settings
from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class EmailTemplate(OrganizationScopedModel, UserTrackedModel):
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ("name",)

    def __str__(self):
        return self.name


class Email(OrganizationScopedModel, UserTrackedModel):
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails",
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    from_email = models.EmailField()
    to_emails = models.JSONField(default=list)
    cc_emails = models.JSONField(default=list, blank=True)
    bcc_emails = models.JSONField(default=list, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.subject


class EmailCampaign(OrganizationScopedModel, UserTrackedModel):
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    recipients = models.JSONField(default=list)
    stats = models.JSONField(default=dict, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name
