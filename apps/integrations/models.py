from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class Webhook(OrganizationScopedModel, UserTrackedModel):
    name = models.CharField(max_length=150)
    url = models.URLField()
    events = models.JSONField(default=list)
    secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("organization", "name")

    def __str__(self):
        return self.name


class IntegrationKey(OrganizationScopedModel):
    name = models.CharField(max_length=150)
    key = models.CharField(max_length=255, unique=True)
    permissions = models.JSONField(default=list, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("organization", "name")

    def __str__(self):
        return self.name
