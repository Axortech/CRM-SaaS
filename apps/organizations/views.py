from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.organizations import services as org_services
from apps.organizations.models import Organization, OrganizationMember, Role
from apps.organizations.serializers import (
    OrganizationCreateSerializer,
    OrganizationMemberSerializer,
    OrganizationMemberUpdateSerializer,
    OrganizationSerializer,
    OrganizationSettingsSerializer,
    RoleSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    schema_tags = ["Organizations"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
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
        return OrganizationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        output_serializer = OrganizationSerializer(
            organization, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        organization = self.get_object()
        if organization.owner_id != self.request.user.id:
            raise PermissionDenied("Only the organization owner can update organization settings.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.id:
            raise PermissionDenied("Only the organization owner can delete the organization.")
        return super().perform_destroy(instance)

    def _ensure_admin(self, organization, user):
        if not org_services.user_is_org_admin(user, organization):
            raise PermissionDenied("Only organization admins can perform this action.")

    def _get_member_by_user(self, organization, user_id):
        try:
            return organization.members.get(user_id=user_id)
        except OrganizationMember.DoesNotExist as exc:
            raise NotFound("Member not found.") from exc

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        organization = self.get_object()
        if request.method == "GET":
            queryset = organization.members.select_related("user", "role").all()
            serializer = OrganizationMemberSerializer(queryset, many=True)
            return Response(serializer.data)

        self._ensure_admin(organization, request.user)
        serializer = OrganizationMemberSerializer(
            data=request.data,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        output_serializer = OrganizationMemberSerializer(member)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"], url_path="members/(?P<user_id>[^/.]+)")
    def member_detail(self, request, pk=None, user_id=None):
        organization = self.get_object()
        self._ensure_admin(organization, request.user)
        member = self._get_member_by_user(organization, user_id)

        if member.user_id == organization.owner_id:
            raise PermissionDenied("Cannot modify the organization owner.")

        if request.method == "DELETE":
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = OrganizationMemberUpdateSerializer(
            member,
            data=request.data,
            partial=True,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrganizationMemberSerializer(member).data)

    @action(detail=True, methods=["patch"], url_path="members/(?P<user_id>[^/.]+)/role")
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
    def roles(self, request, pk=None):
        organization = self.get_object()
        self._ensure_admin(organization, request.user)

        if request.method == "GET":
            roles = organization.roles.all()
            serializer = RoleSerializer(roles, many=True)
            return Response(serializer.data)

        serializer = RoleSerializer(
            data=request.data,
            context={"organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"], url_path="roles/(?P<role_id>[^/.]+)")
    def role_detail(self, request, pk=None, role_id=None):
        organization = self.get_object()
        self._ensure_admin(organization, request.user)

        try:
            role = organization.roles.get(pk=role_id)
        except Role.DoesNotExist:
            raise NotFound("Role not found.")

        if request.method == "DELETE":
            if role.is_system_role:
                raise PermissionDenied("System roles cannot be deleted.")
            role.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def settings(self, request, pk=None):
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
