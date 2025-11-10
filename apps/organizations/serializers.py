from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.organizations.models import Organization, OrganizationMember, Role
from apps.organizations import services as org_services

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "is_system_role", "permissions", "created_at", "updated_at"]
        read_only_fields = ["id", "is_system_role", "created_at", "updated_at"]

    def validate(self, attrs):
        organization = self.context.get("organization")
        name = attrs.get("name")
        if organization and name:
            queryset = Role.objects.filter(organization=organization, name=name)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Role with this name already exists.")
        return attrs

    def create(self, validated_data):
        organization = self.context["organization"]
        validated_data["organization"] = organization
        return super().create(validated_data)


class OrganizationSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "subdomain",
            "owner",
            "owner_email",
            "is_active",
            "timezone",
            "business_hours",
            "logo_url",
            "favicon_url",
            "primary_color",
            "secondary_color",
            "custom_domain",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "owner", "owner_email", "created_at", "updated_at"]


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "timezone", "subdomain", "primary_color", "secondary_color"]
        read_only_fields = ["id"]

    def validate_subdomain(self, value):
        if value and Organization.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("Subdomain already in use.")
        return value

    def create(self, validated_data):
        owner = self.context["request"].user
        organization = org_services.create_organization_with_owner(
            owner=owner,
            name=validated_data["name"],
            timezone=validated_data.get("timezone", "UTC"),
        )
        for field in ["subdomain", "primary_color", "secondary_color"]:
            value = validated_data.get(field)
            if value:
                setattr(organization, field, value)
        organization.save()
        return organization


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "timezone",
            "business_hours",
            "logo_url",
            "favicon_url",
            "primary_color",
            "secondary_color",
            "custom_domain",
        ]


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = OrganizationMember
        fields = [
            "id",
            "user",
            "user_email",
            "role",
            "role_name",
            "is_active",
            "invitation_accepted",
            "joined_at",
        ]
        read_only_fields = ["id", "user_email", "role_name", "joined_at"]

    def validate(self, attrs):
        organization = self.context["organization"]
        user = attrs.get("user")
        if not user:
            raise serializers.ValidationError("User is required.")
        if user == organization.owner:
            raise serializers.ValidationError("Owner is already a member.")
        if OrganizationMember.objects.filter(organization=organization, user=user).exists():
            raise serializers.ValidationError("User is already a member of this organization.")
        if attrs.get("role") and attrs["role"].organization_id != organization.id:
            raise serializers.ValidationError("Role must belong to the same organization.")
        return attrs

    def create(self, validated_data):
        validated_data["organization"] = self.context["organization"]
        return super().create(validated_data)


class OrganizationMemberUpdateSerializer(OrganizationMemberSerializer):
    class Meta(OrganizationMemberSerializer.Meta):
        read_only_fields = ["id", "user", "user_email", "role_name", "joined_at"]

    def validate(self, attrs):
        organization = self.context["organization"]
        role = attrs.get("role")
        if role and role.organization_id != organization.id:
            raise serializers.ValidationError("Role must belong to the same organization.")
        return attrs
