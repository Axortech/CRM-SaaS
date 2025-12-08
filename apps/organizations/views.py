from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.organizations import services as org_services
from apps.organizations.models import Organization, OrganizationMember, Role, Team, Invitation
from apps.organizations.serializers import (
    OrganizationCreateSerializer,
    OrganizationMemberCreateSerializer,
    OrganizationMemberSerializer,
    OrganizationMemberUpdateSerializer,
    OrganizationSerializer,
    OrganizationSettingsSerializer,
    RoleSerializer,
    TeamSerializer,
    TeamMemberAddSerializer,
    InvitationSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing organizations.
    
    Provides endpoints for listing, creating, retrieving, updating, and deleting organizations.
    All operations require authentication.
    """
    schema_tags = ["Organizations"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return organizations where user is owner or active member"""
        user = self.request.user
        return (
            Organization.objects.filter(
                Q(owner=user) | Q(members__user=user, members__is_active=True)
            )
            .distinct()
            .order_by("name")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizationCreateSerializer
        action_serializer_map = {
            "members": OrganizationMemberCreateSerializer,
            "member_detail": OrganizationMemberUpdateSerializer,
            "update_member_role": OrganizationMemberUpdateSerializer,
            "roles": RoleSerializer,
            "role_detail": RoleSerializer,
            "organization_settings": OrganizationSettingsSerializer,
        }
        return action_serializer_map.get(self.action, OrganizationSerializer)

    @extend_schema(
        summary="List organizations",
        description="Get a list of all organizations the authenticated user belongs to.",
        responses={200: OrganizationSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List all organizations for the current user"""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get organization details",
        description="Retrieve detailed information about a specific organization.",
        responses={200: OrganizationSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        """Get organization details"""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create organization",
        description="Create a new organization. The creator is automatically assigned as the owner.",
        request=OrganizationCreateSerializer,
        responses={201: OrganizationSerializer},
    )
    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("Only superadmins can create organizations.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        output_serializer = OrganizationSerializer(
            organization, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response({"data": output_serializer.data}, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        summary="Update organization",
        description="Update organization details. Only the owner can update the organization.",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer},
    )
    def update(self, request, *args, **kwargs):
        """Update organization"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update organization",
        description="Partially update organization details. Only the owner can update the organization.",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update organization"""
        return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        organization = self.get_object()
        if organization.owner_id != self.request.user.id:
            raise PermissionDenied("Only the organization owner can update organization settings.")
        serializer.save()

    @extend_schema(
        summary="Delete organization",
        description="Delete an organization. Only the owner can delete the organization.",
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    def destroy(self, request, *args, **kwargs):
        """Delete organization"""
        instance = self.get_object()
        if instance.owner_id != request.user.id:
            raise PermissionDenied("Only the organization owner can delete the organization.")
        self.perform_destroy(instance)
        return Response({"message": "Organization deleted"}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        """Perform the actual deletion"""
        return super().perform_destroy(instance)

    def _ensure_admin(self, organization, user):
        if not org_services.user_is_org_admin(user, organization):
            raise PermissionDenied("Only organization admins can perform this action.")

    def _get_member_by_user(self, organization, user_id):
        try:
            return organization.members.get(user_id=user_id)
        except OrganizationMember.DoesNotExist as exc:
            raise NotFound("Member not found.") from exc

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="members",
        serializer_class=OrganizationMemberSerializer,
    )
    @extend_schema(
        request=OrganizationMemberCreateSerializer,
        responses=OrganizationMemberSerializer,
        tags=["Organizations"],
        methods=["POST"],
    )
    @extend_schema(
        responses=OrganizationMemberSerializer(many=True),
        tags=["Organizations"],
        methods=["GET"],
    )
    def members(self, request, pk=None):
        """List all members of the organization"""
        organization = self.get_object()
        queryset = organization.members.select_related("user", "role").all()
        
        # Apply filters
        status_filter = request.query_params.get("status")
        if status_filter:
            if status_filter == "active":
                queryset = queryset.filter(is_active=True)
            elif status_filter == "inactive":
                queryset = queryset.filter(is_active=False)
            elif status_filter == "pending":
                queryset = queryset.filter(invitation_accepted=False)
        
        role_id = request.query_params.get("role_id")
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        serializer = OrganizationMemberSerializer(queryset, many=True)
        return Response(serializer.data)

        self._ensure_admin(organization, request.user)
        serializer = self.get_serializer(
            data=request.data,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        output_serializer = OrganizationMemberSerializer(member)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path="members/(?P<user_id>[^/.]+)",
        serializer_class=OrganizationMemberUpdateSerializer,
    )
    @extend_schema(
        request=OrganizationMemberUpdateSerializer,
        responses=OrganizationMemberSerializer,
        tags=["Organizations"],
        methods=["PATCH"],
    )
    @extend_schema(
        responses=None,
        tags=["Organizations"],
        methods=["DELETE"],
    )
    def member_detail(self, request, pk=None, user_id=None):
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            member = organization.members.get(id=member_id)
        except OrganizationMember.DoesNotExist:
            raise NotFound("Member not found.")

        if member.user_id == organization.owner_id:
            raise PermissionDenied("Cannot modify the organization owner.")

        serializer = OrganizationMemberUpdateSerializer(
            member,
            data=request.data,
            partial=True,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrganizationMemberSerializer(member).data)

    @action(
        detail=True,
        methods=["patch"],
        url_path="members/(?P<user_id>[^/.]+)/role",
        serializer_class=OrganizationMemberUpdateSerializer,
    )
    @extend_schema(
        request=OrganizationMemberUpdateSerializer,
        responses=OrganizationMemberSerializer,
        tags=["Organizations"],
    )
    def update_member_role(self, request, pk=None, user_id=None):
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        member = self._get_member_by_user(organization, user_id)
        serializer = OrganizationMemberUpdateSerializer(
            member,
            data={"role": request.data.get("role")},
            partial=True,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrganizationMemberSerializer(member).data)

    @action(detail=True, methods=["get", "post"], url_path="roles")
    @extend_schema(
        request=RoleSerializer,
        responses=RoleSerializer,
        tags=["Organizations"],
        methods=["POST"],
    )
    @extend_schema(
        responses=RoleSerializer(many=True),
        tags=["Organizations"],
        methods=["GET"],
    )
    def roles(self, request, pk=None):
        """List all roles in the organization"""
        organization = self.get_object()
        roles = organization.roles.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create custom role",
        description="Create a new custom role. Cannot create system roles.",
        request=RoleSerializer,
        responses={201: RoleSerializer},
    )
    @action(detail=True, methods=["post"], url_path="roles")
    def create_role(self, request, pk=None):
        """Create a new custom role"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        serializer = RoleSerializer(
            data=request.data,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"], url_path="roles/(?P<role_id>[^/.]+)")
    @extend_schema(
        request=RoleSerializer,
        responses=RoleSerializer,
        tags=["Organizations"],
        methods=["PATCH"],
    )
    @extend_schema(
        responses=None,
        tags=["Organizations"],
        methods=["DELETE"],
    )
    def role_detail(self, request, pk=None, role_id=None):
        """Get role details"""
        organization = self.get_object()
        try:
            role = organization.roles.get(pk=role_id)
        except Role.DoesNotExist:
            raise NotFound("Role not found.")
        serializer = RoleSerializer(role)
        return Response(serializer.data)

    @extend_schema(
        summary="Update role",
        description="Update a role. Cannot update system roles.",
        request=RoleSerializer,
        responses={200: RoleSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="roles/(?P<role_id>[^/.]+)")
    def update_role(self, request, pk=None, role_id=None):
        """Update role"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            role = organization.roles.get(pk=role_id)
        except Role.DoesNotExist:
            raise NotFound("Role not found.")

        if role.is_system_role and any(field in request.data for field in ["name"]):
            raise ValidationError("System role names cannot be modified.")

        serializer = RoleSerializer(
            role,
            data=request.data,
            partial=True,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RoleSerializer(role).data)

    @action(detail=True, methods=["get", "patch"], url_path="settings", url_name="settings")
    def organization_settings(self, request, pk=None):
        organization = self.get_object()
        if request.method == "GET":
            serializer = OrganizationSettingsSerializer(organization)
            return Response(serializer.data)
        self._ensure_admin(organization, request.user)
        serializer = OrganizationSettingsSerializer(
            organization, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        summary="Upload organization logo",
        description="Upload a logo image for the organization.",
        request={"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}},
        responses={200: {"type": "object", "properties": {"logo_url": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post"], url_path="logo")
    def upload_logo(self, request, pk=None):
        """Upload organization logo"""
        organization = self.get_object()
        
        # Check permissions - only owner or admin can upload logo
        if organization.owner_id != request.user.id:
            self._ensure_admin(organization, request.user)
        
        if "file" not in request.FILES:
            return Response(
                {"error": "File is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES["file"]
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if uploaded_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Only image files are allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return Response(
                {"error": "File size exceeds 5MB limit."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save file (in production, this would upload to S3/CDN)
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Generate filename
        file_ext = os.path.splitext(uploaded_file.name)[1] or ".png"
        filename = f"logos/org_{organization.id}{file_ext}"
        
        # Save file
        file_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
        
        # Get file URL
        # In production, this would be a CDN URL
        logo_url = default_storage.url(file_path)
        
        # Update organization
        organization.logo_url = logo_url
        organization.save(update_fields=["logo_url"])
        
        return Response({"logo_url": logo_url}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="List teams",
        description="Get a list of all teams in the organization.",
        responses={200: TeamSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="teams")
    def teams(self, request, pk=None):
        """List all teams in the organization"""
        organization = self.get_object()
        teams = Team.objects.filter(organization=organization)
        serializer = TeamSerializer(teams, many=True, context={"organization": organization})
        return Response(serializer.data)

    @extend_schema(
        summary="Create team",
        description="Create a new team in the organization.",
        request=TeamSerializer,
        responses={201: TeamSerializer},
    )
    @action(detail=True, methods=["post"], url_path="teams")
    def create_team(self, request, pk=None):
        """Create a new team"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        serializer = TeamSerializer(
            data=request.data,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        team = serializer.save()
        return Response(TeamSerializer(team, context={"organization": organization}).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Get team details",
        description="Retrieve detailed information about a specific team.",
        responses={200: TeamSerializer},
    )
    @action(detail=True, methods=["get"], url_path="teams/(?P<team_id>[^/.]+)")
    def team_detail(self, request, pk=None, team_id=None):
        """Get team details"""
        organization = self.get_object()
        try:
            team = Team.objects.get(id=team_id, organization=organization)
        except Team.DoesNotExist:
            raise NotFound("Team not found.")
        serializer = TeamSerializer(team, context={"organization": organization})
        return Response(serializer.data)

    @extend_schema(
        summary="Update team",
        description="Update team information.",
        request=TeamSerializer,
        responses={200: TeamSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="teams/(?P<team_id>[^/.]+)")
    def update_team(self, request, pk=None, team_id=None):
        """Update team"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            team = Team.objects.get(id=team_id, organization=organization)
        except Team.DoesNotExist:
            raise NotFound("Team not found.")
        
        serializer = TeamSerializer(
            team,
            data=request.data,
            partial=True,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TeamSerializer(team, context={"organization": organization}).data)

    @extend_schema(
        summary="Delete team",
        description="Delete a team from the organization.",
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    @action(detail=True, methods=["delete"], url_path="teams/(?P<team_id>[^/.]+)")
    def delete_team(self, request, pk=None, team_id=None):
        """Delete team"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            team = Team.objects.get(id=team_id, organization=organization)
        except Team.DoesNotExist:
            raise NotFound("Team not found.")
        
        team.delete()
        return Response({"message": "Team deleted"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add members to team",
        description="Add one or more members to a team.",
        request=TeamMemberAddSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post"], url_path="teams/(?P<team_id>[^/.]+)/members")
    def add_team_members(self, request, pk=None, team_id=None):
        """Add members to team"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            team = Team.objects.get(id=team_id, organization=organization)
        except Team.DoesNotExist:
            raise NotFound("Team not found.")
        
        serializer = TeamMemberAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        member_ids = serializer.validated_data["member_ids"]
        members = OrganizationMember.objects.filter(
            id__in=member_ids,
            organization=organization
        )
        team.members.add(*members)
        
        return Response({"message": "Members added"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Remove member from team",
        description="Remove a member from a team.",
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    @action(detail=True, methods=["delete"], url_path="teams/(?P<team_id>[^/.]+)/members/(?P<member_id>[^/.]+)")
    def remove_team_member(self, request, pk=None, team_id=None, member_id=None):
        """Remove member from team"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            team = Team.objects.get(id=team_id, organization=organization)
        except Team.DoesNotExist:
            raise NotFound("Team not found.")
        
        try:
            member = organization.members.get(id=member_id)
        except OrganizationMember.DoesNotExist:
            raise NotFound("Member not found.")
        
        team.members.remove(member)
        return Response({"message": "Member removed"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="List invitations",
        description="Get a list of all invitations for the organization.",
        parameters=[
            OpenApiParameter("status", str, description="Filter by status (pending, accepted, expired, cancelled)"),
        ],
        responses={200: InvitationSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="invitations")
    def invitations(self, request, pk=None):
        """List all invitations for the organization"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        
        queryset = Invitation.objects.filter(organization=organization).select_related("role", "invited_by").prefetch_related("teams")
        
        # Apply status filter
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = InvitationSerializer(queryset, many=True, context={"organization": organization, "request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Send invitation",
        description="Send an invitation to join the organization. An email will be sent with the invitation link.",
        request=InvitationSerializer,
        responses={201: InvitationSerializer},
    )
    @action(detail=True, methods=["post"], url_path="invitations")
    def send_invitation(self, request, pk=None):
        """Send invitation"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        serializer = InvitationSerializer(
            data=request.data,
            context={"organization": organization, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        return Response(InvitationSerializer(invitation, context={"organization": organization, "request": request}).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Get invitation details",
        description="Retrieve detailed information about a specific invitation.",
        responses={200: InvitationSerializer},
    )
    @action(detail=True, methods=["get"], url_path="invitations/(?P<invitation_id>[^/.]+)")
    def invitation_detail(self, request, pk=None, invitation_id=None):
        """Get invitation details"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            invitation = Invitation.objects.get(id=invitation_id, organization=organization)
        except Invitation.DoesNotExist:
            raise NotFound("Invitation not found.")
        serializer = InvitationSerializer(invitation, context={"organization": organization, "request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Cancel invitation",
        description="Cancel a pending invitation.",
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post", "patch"], url_path="invitations/(?P<invitation_id>[^/.]+)/cancel")
    def cancel_invitation(self, request, pk=None, invitation_id=None):
        """Cancel invitation"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            invitation = Invitation.objects.get(id=invitation_id, organization=organization)
        except Invitation.DoesNotExist:
            raise NotFound("Invitation not found.")
        
        if invitation.status != Invitation.Status.PENDING:
            raise ValidationError("Only pending invitations can be cancelled.")
        
        invitation.cancel()
        return Response({"message": "Invitation cancelled"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Resend invitation",
        description="Resend an invitation email.",
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post"], url_path="invitations/(?P<invitation_id>[^/.]+)/resend")
    def resend_invitation(self, request, pk=None, invitation_id=None):
        """Resend invitation"""
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        try:
            invitation = Invitation.objects.get(id=invitation_id, organization=organization)
        except Invitation.DoesNotExist:
            raise NotFound("Invitation not found.")
        
        if invitation.status != Invitation.Status.PENDING:
            raise ValidationError("Only pending invitations can be resent.")
        
        # TODO: Resend invitation email
        
        return Response({"message": "Invitation resent"}, status=status.HTTP_200_OK)
