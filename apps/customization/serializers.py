from rest_framework import serializers

from apps.customization.models import CustomField, LayoutConfiguration


class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = [
            "id",
            "organization",
            "entity_type",
            "field_name",
            "field_label",
            "field_type",
            "options",
            "is_required",
            "default_value",
            "order",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]


class LayoutConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayoutConfiguration
        fields = [
            "id",
            "organization",
            "user",
            "page_type",
            "configuration",
            "is_default",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        organization = self.context.get("organization") or getattr(self.instance, "organization", None)
        user = attrs.get("user")
        if user and organization and not organization.members.filter(user=user, is_active=True).exists() and organization.owner_id != user.id:
            raise serializers.ValidationError("User must belong to the organization.")
        return attrs
