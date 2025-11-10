from rest_framework import serializers

from apps.notifications.models import AuditLogEntry, Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "organization",
            "user",
            "notification_type",
            "title",
            "message",
            "link",
            "is_read",
            "read_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLogEntry
        fields = [
            "id",
            "organization",
            "user",
            "action",
            "entity_type",
            "entity_id",
            "changes",
            "ip_address",
            "user_agent",
            "timestamp",
        ]
        read_only_fields = fields
