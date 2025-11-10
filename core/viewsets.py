from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations import services as org_services
from apps.organizations.models import Organization


class OrganizationScopedViewSet(viewsets.ModelViewSet):
    organization_param = "organization"
    organization_field = "organization_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        org_ids = org_services.organization_ids_for_user(self.request.user)
        queryset = queryset.filter(**{f"{self.organization_field}__in": org_ids})
        org_param = self.request.query_params.get(self.organization_param)
        if org_param:
            queryset = queryset.filter(**{self.organization_field: org_param})
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        organization = self._get_request_organization()
        if organization:
            context["organization"] = organization
        return context

    def _get_request_organization(self):
        if hasattr(self, "_request_organization"):
            return self._request_organization
        org_id = None
        data = getattr(self.request, "data", None)
        if data and hasattr(data, "get"):
            org_id = data.get(self.organization_param)
        org_id = (
            org_id
            or self.request.query_params.get(self.organization_param)
            or self.kwargs.get("organization_id")
        )
        organization = None
        if org_id:
            try:
                organization = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist as exc:
                raise ValidationError({"organization": "Organization not found."}) from exc
            if not org_services.user_in_organization(self.request.user, organization):
                raise PermissionDenied("You do not have access to this organization.")
        self._request_organization = organization
        return organization

    def perform_create(self, serializer):
        organization = self._get_request_organization()
        if organization is None:
            raise ValidationError({"organization": "This field is required."})
        extra = {}
        model_class = getattr(getattr(serializer, "Meta", None), "model", None)
        if model_class and hasattr(model_class, "created_by"):
            extra["created_by"] = self.request.user if self.request.user.is_authenticated else None
        serializer.save(
            organization=organization,
            **extra,
        )
