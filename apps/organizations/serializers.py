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
    admin_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        help_text="User who will be assigned as the organization admin.",
    )

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "timezone",
            "subdomain",
            "primary_color",
            "secondary_color",
            "admin_user",
        ]
        read_only_fields = ["id"]

    def validate_subdomain(self, value):
        if value and Organization.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("Subdomain already in use.")
        return value

    def create(self, validated_data):
        owner = self.context["request"].user
        admin_user = validated_data.pop("admin_user")
        organization = org_services.create_organization_with_owner(
            owner=owner,
            name=validated_data["name"],
            timezone=validated_data.get("timezone", "UTC"),
            admin_user=admin_user,
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


class OrganizationMemberCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        help_text="Existing user ID to add. If omitted, a new user will be created.",
    )
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = OrganizationMember
        fields = [
            "id",
            "user",
            "email",
            "first_name",
            "last_name",
            "password",
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
        email = attrs.get("email")
        role = attrs.get("role")

        if user:
            if user == organization.owner:
                raise serializers.ValidationError("Owner is already a member.")
            if OrganizationMember.objects.filter(organization=organization, user=user).exists():
                raise serializers.ValidationError("User is already a member of this organization.")
        else:
            if not email:
                raise serializers.ValidationError({"email": "Email is required when user is not provided."})
            try:
                existing_user = User.objects.get(email=email)
            except User.DoesNotExist:
                existing_user = None
            if existing_user and OrganizationMember.objects.filter(
                organization=organization, user=existing_user
            ).exists():
                raise serializers.ValidationError("User is already a member of this organization.")
            attrs["existing_user"] = existing_user

        if role and role.organization_id != organization.id:
            raise serializers.ValidationError("Role must belong to the same organization.")
        return attrs

    def create(self, validated_data):
        organization = self.context["organization"]
        role = validated_data.get("role")
        user = validated_data.pop("user", None)
        existing_user = validated_data.pop("existing_user", None)

        if not user:
            user = existing_user

        if not user:
            # Create a new user
            email = validated_data.pop("email")
            password = validated_data.pop("password", None)
            first_name = validated_data.pop("first_name", "")
            last_name = validated_data.pop("last_name", "")
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
        elif "email" in validated_data:
            # Clean up unused fields if user was supplied
            validated_data.pop("email", None)
            validated_data.pop("password", None)
            validated_data.pop("first_name", None)
            validated_data.pop("last_name", None)

        return OrganizationMember.objects.create(
            organization=organization,
            user=user,
            role=role,
            is_active=validated_data.get("is_active", True),
            invitation_accepted=validated_data.get("invitation_accepted", False),
        )


class OrganizationMemberUpdateSerializer(OrganizationMemberSerializer):
    class Meta(OrganizationMemberSerializer.Meta):
        read_only_fields = ["id", "user", "user_email", "role_name", "joined_at"]

    def validate(self, attrs):
        organization = self.context["organization"]
        role = attrs.get("role")
        if role and role.organization_id != organization.id:
            raise serializers.ValidationError("Role must belong to the same organization.")
        return attrs
