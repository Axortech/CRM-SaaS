from rest_framework import serializers

from apps.integrations.models import IntegrationKey, Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = [
            "id",
            "organization",
            "name",
            "url",
            "events",
            "secret",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]


class IntegrationKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationKey
        fields = [
            "id",
            "organization",
            "name",
            "key",
            "permissions",
            "last_used_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "last_used_at", "created_at", "updated_at"]
