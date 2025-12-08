from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import FilterSet, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.activities.models import Activity
from apps.activities.serializers import ActivitySerializer
from apps.contacts.models import Contact
from apps.leads.models import Lead


class ActivityFilterSet(FilterSet):
    activity_type = filters.CharFilter(field_name="activity_type")
    contact = filters.UUIDFilter(field_name="contact_id")
    company = filters.UUIDFilter(field_name="company_id")
    opportunity = filters.UUIDFilter(field_name="opportunity_id")
    lead = filters.UUIDFilter(field_name="lead_id")
    occurred_before = filters.DateTimeFilter(field_name="occurred_at", lookup_expr="lte")
    occurred_after = filters.DateTimeFilter(field_name="occurred_at", lookup_expr="gte")

    class Meta:
        model = Activity
        fields = ["activity_type", "contact", "company", "opportunity", "lead"]


class ActivityViewSet(OrganizationScopedViewSet):
    """
    ViewSet for managing activities.
    
    Activities can be associated with contacts, leads, companies, or opportunities.
    """
    schema_tags = ["Activities"]
    queryset = Activity.objects.select_related("contact", "company", "opportunity", "lead", "created_by")
    serializer_class = ActivitySerializer
    filterset_class = ActivityFilterSet
    search_fields = ["subject", "description"]
    ordering_fields = ["occurred_at", "created_at"]
    ordering = ["-occurred_at"]
    
    @extend_schema(
        summary="List activities",
        description="Get a paginated list of activities with filtering capabilities.",
        responses={200: ActivitySerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List activities"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get activity details",
        description="Retrieve detailed information about a specific activity.",
        responses={200: ActivitySerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        """Get activity details"""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create activity",
        description="Create a new activity. Can be associated with a contact, lead, company, or opportunity.",
        request=ActivitySerializer,
        responses={201: ActivitySerializer},
    )
    def create(self, request, *args, **kwargs):
        """Create activity"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = request.data.copy()
        
        # Handle entity_type and entity_id format
        entity_type = data.get("entity_type")
        entity_id = data.get("entity_id")
        
        if entity_type and entity_id:
            # Map entity_type and entity_id to appropriate foreign key
            if entity_type == "contact":
                try:
                    contact = Contact.objects.get(id=entity_id, organization=organization)
                    data["contact"] = str(contact.id)
                except Contact.DoesNotExist:
                    return Response(
                        {"error": "Contact not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif entity_type == "lead":
                try:
                    lead = Lead.objects.get(id=entity_id, organization=organization)
                    data["lead"] = str(lead.id)
                except Lead.DoesNotExist:
                    return Response(
                        {"error": "Lead not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            # Remove entity_type and entity_id from data as they're not model fields
            data.pop("entity_type", None)
            data.pop("entity_id", None)
        
        # Map type to activity_type and title to subject
        if "type" in data:
            data["activity_type"] = data.pop("type")
        if "title" in data:
            data["subject"] = data.pop("title")
        
        serializer = self.get_serializer(data=data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        activity = serializer.save(organization=organization, created_by=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
