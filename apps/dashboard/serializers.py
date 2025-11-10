from rest_framework import serializers

from apps.dashboard.models import DashboardWidget


class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = [
            "id",
            "organization",
            "title",
            "widget_type",
            "configuration",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]
