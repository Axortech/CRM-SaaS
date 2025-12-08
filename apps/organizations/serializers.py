from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.organizations.models import Organization, OrganizationMember, Role, Team, Invitation
from apps.organizations import services as org_services

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True)
    is_default = serializers.SerializerMethodField()
    is_system = serializers.BooleanField(source="is_system_role", read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "is_default",
            "is_system",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_is_default(self, obj):
        """Check if this is the default role for the organization"""
        # You can implement logic to determine default role
        return False

    def get_permissions(self, obj):
        """Format permissions to match requirements structure"""
        if isinstance(obj.permissions, dict):
            return obj.permissions
        # If permissions is a list, convert to dict format
        # Default structure based on requirements
        return {
            "contacts": [],
            "leads": [],
            "deals": [],
            "tasks": [],
            "reports": [],
            "settings": [],
            "team": [],
            "organization": [],
        }

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
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)
    settings = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "logo_url",
            "owner_id",
            "settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "owner_id", "created_at", "updated_at"]

    def get_settings(self, obj):
        """Extract settings from organization fields and business_hours JSON"""
        # Get default role if exists
        default_role = obj.roles.filter(is_system_role=True).first()
        return {
            "default_role_id": str(default_role.id) if default_role else None,
            "allow_member_invites": True,  # Default value
            "require_two_factor": False,  # Default value
            "timezone": obj.timezone or "UTC",
            "date_format": "MM/DD/YYYY",  # Default value
            "currency": "USD",  # Default value
        }


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
        # Set additional fields if provided
        for field in ["industry", "size", "website"]:
            if field in validated_data:
                setattr(organization, field, validated_data[field])
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
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    avatar_url = serializers.CharField(source="user.avatar_url", read_only=True, allow_null=True)
    job_title = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    status = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    teams = serializers.SerializerMethodField()
    last_active_at = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = OrganizationMember
        fields = [
            "id",
            "user_id",
            "organization_id",
            "email",
            "first_name",
            "last_name",
            "avatar_url",
            "job_title",
            "phone",
            "status",
            "role",
            "teams",
            "joined_at",
            "last_active_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "organization_id",
            "email",
            "first_name",
            "last_name",
            "avatar_url",
            "joined_at",
        ]

    def get_status(self, obj):
        """Map member status based on is_active and invitation_accepted"""
        if not obj.is_active:
            return "inactive"
        if not obj.invitation_accepted:
            return "pending"
        return "active"

    def get_role(self, obj):
        """Format role information"""
        if obj.role:
            return {
                "id": str(obj.role.id),
                "name": obj.role.name,
                "description": getattr(obj.role, "description", ""),
                "permissions": obj.role.permissions if isinstance(obj.role.permissions, dict) else {},
            }
        return None

    def get_teams(self, obj):
        """Get teams for the member"""
        teams = obj.teams.all()
        return [
            {
                "id": str(team.id),
                "name": team.name,
            }
            for team in teams
        ]

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


class TeamSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    leader_id = serializers.UUIDField(source="leader.id", read_only=True, allow_null=True)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Team
        fields = [
            "id",
            "organization_id",
            "name",
            "description",
            "color",
            "leader_id",
            "member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "member_count", "created_at", "updated_at"]

    def validate(self, attrs):
        organization = self.context.get("organization")
        name = attrs.get("name")
        if organization and name:
            queryset = Team.objects.filter(organization=organization, name=name)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Team with this name already exists.")
        return attrs

    def create(self, validated_data):
        organization = self.context["organization"]
        validated_data["organization"] = organization
        team = super().create(validated_data)
        
        # Add members if provided
        member_ids = self.initial_data.get("member_ids", [])
        if member_ids:
            members = OrganizationMember.objects.filter(
                id__in=member_ids,
                organization=organization
            )
            team.members.set(members)
        
        return team

    def update(self, instance, validated_data):
        team = super().update(instance, validated_data)
        
        # Update members if provided
        if "member_ids" in self.initial_data:
            member_ids = self.initial_data.get("member_ids")
            if member_ids is not None:
                members = OrganizationMember.objects.filter(
                    id__in=member_ids,
                    organization=team.organization
                )
                team.members.set(members)
        
        return team


class TeamMemberAddSerializer(serializers.Serializer):
    """Serializer for adding members to a team"""
    member_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of member IDs to add to the team"
    )

    def validate_member_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one member ID is required.")
        return value


class InvitationSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    role_id = serializers.UUIDField(source="role.id", read_only=True, allow_null=True)
    team_ids = serializers.SerializerMethodField()
    invited_by = serializers.UUIDField(source="invited_by.id", read_only=True, allow_null=True)
    token = serializers.CharField(read_only=True)

    class Meta:
        model = Invitation
        fields = [
            "id",
            "organization_id",
            "email",
            "role_id",
            "team_ids",
            "status",
            "invited_by",
            "invited_at",
            "expires_at",
            "accepted_at",
            "token",
            "message",
        ]
        read_only_fields = [
            "id",
            "organization_id",
            "invited_by",
            "token",
            "invited_at",
            "expires_at",
            "accepted_at",
            "status",
        ]

    def get_team_ids(self, obj):
        """Get team IDs for the invitation"""
        return [str(team.id) for team in obj.teams.all()]

    def validate(self, attrs):
        organization = self.context.get("organization")
        email = attrs.get("email")
        
        if organization and email:
            # Check if user is already a member
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                if OrganizationMember.objects.filter(organization=organization, user=user).exists():
                    raise serializers.ValidationError("User is already a member of this organization.")
            except User.DoesNotExist:
                pass
            
            # Check for pending invitation
            if Invitation.objects.filter(
                organization=organization,
                email=email,
                status=Invitation.Status.PENDING
            ).exists():
                raise serializers.ValidationError("A pending invitation already exists for this email.")
        
        return attrs

    def create(self, validated_data):
        import secrets
        from datetime import timedelta
        from django.utils import timezone
        
        organization = self.context["organization"]
        validated_data["organization"] = organization
        validated_data["invited_by"] = self.context["request"].user
        
        # Generate unique token
        token = secrets.token_urlsafe(32)
        while Invitation.objects.filter(token=token).exists():
            token = secrets.token_urlsafe(32)
        validated_data["token"] = token
        
        # Set expiration (7 days from now)
        validated_data["expires_at"] = timezone.now() + timedelta(days=7)
        
        invitation = super().create(validated_data)
        
        # Add teams if provided
        team_ids = self.initial_data.get("team_ids", [])
        if team_ids:
            teams = Team.objects.filter(id__in=team_ids, organization=organization)
            invitation.teams.set(teams)
        
        # TODO: Send invitation email
        
        return invitation


class InvitationAcceptSerializer(serializers.Serializer):
    """Serializer for accepting an invitation"""
    user_id = serializers.UUIDField(required=False, allow_null=True)
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    password = serializers.CharField(required=False, min_length=8, write_only=True)

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        password = attrs.get("password")
        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")
        
        # Either user_id or create new user (first_name, last_name, password)
        if user_id:
            if password or first_name or last_name:
                raise serializers.ValidationError("Cannot provide user_id with password or name fields.")
        else:
            if not password or not first_name:
                raise serializers.ValidationError("Either user_id or (first_name, last_name, password) is required.")
        
        return attrs
