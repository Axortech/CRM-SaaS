from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.companies.models import Company
from apps.contacts.models import Contact, Tag

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color", "organization", "created_at", "updated_at"]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


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
            "tags",
            "custom_fields",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]

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
    ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    data = serializers.DictField(child=serializers.CharField(), required=False)


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
