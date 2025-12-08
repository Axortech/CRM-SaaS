from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.companies.models import Company
from apps.contacts.models import Contact, Tag

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ["id", "organization_id", "name", "color", "usage_count", "created_at", "updated_at"]
        read_only_fields = ["id", "organization_id", "usage_count", "created_at", "updated_at"]

    def get_usage_count(self, obj):
        """Get the number of contacts using this tag"""
        return obj.contacts.count()


class ContactSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        allow_null=True,
        required=False,
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )
    avatar_url = serializers.SerializerMethodField()
    assigned_to = serializers.UUIDField(source="owner.id", read_only=True, allow_null=True)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = [
            "id",
            "organization",
            "first_name",
            "last_name",
            "email",
            "phone",
            "mobile",
            "company",
            "job_title",
            "stage",
            "source",
            "owner",
            "assigned_to",
            "assigned_to_name",
            "tags",
            "avatar_url",
            "custom_fields",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "assigned_to", "assigned_to_name", "avatar_url", "created_at", "updated_at"]
    
    def get_avatar_url(self, obj):
        """Get avatar URL from custom_fields"""
        if obj.custom_fields and "avatar_url" in obj.custom_fields:
            return obj.custom_fields["avatar_url"]
        return None
    
    def get_assigned_to_name(self, obj):
        """Get assigned user's name"""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return None

    def _get_organization(self):
        organization = self.context.get("organization")
        if organization:
            return organization
        instance = getattr(self, "instance", None)
        if instance:
            return instance.organization
        return None

    def validate_company(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and value.organization_id != organization.id:
            raise serializers.ValidationError("Company must belong to the same organization.")
        return value

    def validate_owner(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and not organization.members.filter(user=value, is_active=True).exists() and organization.owner_id != value.id:
            raise serializers.ValidationError("Owner must be a member of the organization.")
        return value

    def validate_tags(self, value):
        organization = self._get_organization()
        for tag in value:
            if organization and tag.organization_id != organization.id:
                raise serializers.ValidationError("Tags must belong to the same organization.")
        return value

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        contact = super().create(validated_data)
        if tags:
            contact.tags.set(tags)
        return contact


class ContactBulkImportSerializer(serializers.Serializer):
    contacts = ContactSerializer(many=True)


class ContactBulkOperationSerializer(serializers.Serializer):
    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of contact IDs"
    )
    updates = serializers.DictField(
        required=False,
        help_text="Fields to update for all selected contacts"
    )


class ContactMergeSerializer(serializers.Serializer):
    primary_id = serializers.UUIDField()
    secondary_id = serializers.UUIDField()

    def validate(self, attrs):
        if attrs["primary_id"] == attrs["secondary_id"]:
            raise serializers.ValidationError("Primary and secondary contacts must differ.")
        return attrs

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        contact = super().update(instance, validated_data)
        if tags is not None:
            contact.tags.set(tags)
        return contact
