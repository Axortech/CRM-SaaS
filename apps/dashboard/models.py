from django.db import models

from core.models import OrganizationScopedModel, UserTrackedModel


class DashboardWidget(OrganizationScopedModel, UserTrackedModel):
    title = models.CharField(max_length=150)
    widget_type = models.CharField(max_length=64)
    configuration = models.JSONField(default=dict)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return self.title
