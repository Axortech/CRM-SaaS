from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django_filters.rest_framework import FilterSet, filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.viewsets import OrganizationScopedViewSet
from apps.activities.models import Activity
from apps.contacts.models import Contact, Tag
from apps.contacts.serializers import ContactSerializer
from apps.leads.models import Lead
from apps.leads.serializers import (
    LeadConvertSerializer,
    LeadScoreUpdateSerializer,
    LeadSerializer,
    LeadStatusUpdateSerializer,
)


class LeadFilterSet(FilterSet):
    status = filters.CharFilter(field_name="status")
    source = filters.CharFilter(field_name="source")
    priority = filters.CharFilter(field_name="priority")
    assigned_to = filters.UUIDFilter(field_name="assigned_to_id")
    tags = filters.UUIDFilter(field_name="tags__id")
    score_min = filters.NumberFilter(field_name="score", lookup_expr="gte")
    score_max = filters.NumberFilter(field_name="score", lookup_expr="lte")
    created_from = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_to = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    
    class Meta:
        model = Lead
        fields = ["status", "source", "priority", "assigned_to", "tags", "score_min", "score_max", "created_from", "created_to"]


class LeadViewSet(OrganizationScopedViewSet):
    """
    ViewSet for managing leads.
    
    Provides endpoints for listing, creating, retrieving, updating, and deleting leads.
    Also includes endpoints for status updates, score updates, conversion, and statistics.
    """
    schema_tags = ["Leads"]
    queryset = Lead.objects.select_related("assigned_to__user", "contact", "converted_to_contact").prefetch_related("tags")
    serializer_class = LeadSerializer
    filterset_class = LeadFilterSet
    search_fields = ["name", "email", "company"]
    ordering_fields = ["name", "score", "priority", "created_at", "updated_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Filter leads by organization"""
        queryset = super().get_queryset()
        organization = self._get_request_organization()
        if organization:
            return queryset.filter(organization=organization)
        return queryset
    
    @extend_schema(
        summary="List leads",
        description="Get a paginated list of leads with filtering and search capabilities.",
        parameters=[
            OpenApiParameter("status", str, description="Filter by status (new, contacted, qualified, unqualified, converted)"),
            OpenApiParameter("source", str, description="Filter by source"),
            OpenApiParameter("priority", str, description="Filter by priority (low, medium, high, urgent)"),
            OpenApiParameter("assigned_to", str, description="Filter by assigned member ID"),
            OpenApiParameter("tags", str, description="Filter by tag IDs (comma-separated)"),
            OpenApiParameter("score_min", int, description="Minimum lead score (0-100)"),
            OpenApiParameter("score_max", int, description="Maximum lead score (0-100)"),
            OpenApiParameter("created_from", str, description="Filter by created date from (ISO date)"),
            OpenApiParameter("created_to", str, description="Filter by created date to (ISO date)"),
        ],
        responses={200: LeadSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List leads with filters"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get lead details",
        description="Retrieve detailed information about a specific lead.",
        responses={200: LeadSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        """Get lead details"""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create lead",
        description="Create a new lead. Score will default to 0 if not provided.",
        request=LeadSerializer,
        responses={201: LeadSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Create a new lead"""
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update lead",
        description="Update lead information.",
        request=LeadSerializer,
        responses={200: LeadSerializer},
    )
    def update(self, request, *args, **kwargs):
        """Update lead"""
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partially update lead",
        description="Partially update lead information.",
        request=LeadSerializer,
        responses={200: LeadSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update lead"""
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete lead",
        description="Delete a lead.",
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    )
    def destroy(self, request, *args, **kwargs):
        """Delete lead"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Lead deleted"}, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Get leads by status (Kanban)",
        description="Get leads grouped by status for Kanban board view.",
        responses={200: {"type": "object"}},
    )
    @action(detail=False, methods=["get"], url_path="by-status")
    def by_status(self, request, *args, **kwargs):
        """Get leads grouped by status"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(organization=organization)
        queryset = self.filter_queryset(queryset)
        
        # Group by status
        result = {
            "new": [],
            "contacted": [],
            "qualified": [],
            "unqualified": [],
            "converted": [],
        }
        
        for lead in queryset:
            serializer = LeadSerializer(lead, context=self.get_serializer_context())
            status_key = lead.status
            if status_key in result:
                result[status_key].append(serializer.data)
        
        return Response(result)
    
    @extend_schema(
        summary="Update lead status",
        description="Update the status of a lead. If status is 'converted', converted_at will be set.",
        request=LeadStatusUpdateSerializer,
        responses={200: LeadSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """Update lead status"""
        lead = self.get_object()
        serializer = LeadStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data["status"]
        lead.status = new_status
        
        # Set converted_at if status is converted
        if new_status == Lead.Status.CONVERTED and not lead.converted_at:
            from django.utils import timezone
            lead.converted_at = timezone.now()
            lead.save(update_fields=["status", "converted_at"])
        else:
            lead.save(update_fields=["status"])
        
        return Response(LeadSerializer(lead, context=self.get_serializer_context()).data)
    
    @extend_schema(
        summary="Update lead score",
        description="Update the score of a lead (0-100).",
        request=LeadScoreUpdateSerializer,
        responses={200: LeadSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="score")
    def update_score(self, request, pk=None):
        """Update lead score"""
        lead = self.get_object()
        serializer = LeadScoreUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lead.score = serializer.validated_data["score"]
        lead.save(update_fields=["score"])
        
        return Response(LeadSerializer(lead, context=self.get_serializer_context()).data)
    
    @extend_schema(
        summary="Convert lead to contact",
        description="Convert a lead to a contact. Creates a new contact if create_contact is true.",
        request=LeadConvertSerializer,
        responses={200: {"type": "object"}},
    )
    @action(detail=True, methods=["post"], url_path="convert")
    def convert(self, request, pk=None):
        """Convert lead to contact"""
        lead = self.get_object()
        organization = self._get_request_organization()
        
        serializer = LeadConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        create_contact = serializer.validated_data.get("create_contact", True)
        contact_data = serializer.validated_data.get("contact_data", {})
        
        contact = None
        if create_contact:
            # Create contact from lead data
            contact_serializer_data = {
                "first_name": contact_data.get("first_name") or lead.name.split()[0] if lead.name else "",
                "last_name": contact_data.get("last_name") or " ".join(lead.name.split()[1:]) if lead.name and len(lead.name.split()) > 1 else "",
                "email": contact_data.get("email") or lead.email,
                "phone": contact_data.get("phone") or lead.phone,
                "job_title": contact_data.get("job_title") or lead.job_title,
                "source": lead.source or "",
                "stage": Contact.Stage.PROSPECT,
            }
            
            contact_serializer = ContactSerializer(
                data=contact_serializer_data,
                context={"organization": organization}
            )
            contact_serializer.is_valid(raise_exception=True)
            contact = contact_serializer.save(organization=organization, created_by=request.user)
            
            # Copy tags
            if lead.tags.exists():
                contact.tags.set(lead.tags.all())
        
        # Mark lead as converted
        lead.mark_converted(contact)
        
        return Response({
            "lead": LeadSerializer(lead, context=self.get_serializer_context()).data,
            "contact": ContactSerializer(contact, context={"organization": organization}).data if contact else None,
            "message": "Lead converted to contact"
        })
    
    @extend_schema(
        summary="Get lead statistics",
        description="Get comprehensive statistics about leads in the organization.",
        responses={200: {"type": "object"}},
    )
    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request, *args, **kwargs):
        """Get lead statistics"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(organization=organization)
        
        # Total count
        total = queryset.count()
        
        # By status
        by_status = {}
        for status_value, status_label in Lead.Status.choices:
            count = queryset.filter(status=status_value).count()
            by_status[status_value] = count
        
        # By source
        by_source = {}
        for source_value, source_label in Lead.Source.choices:
            count = queryset.filter(source=source_value).count()
            if count > 0:
                by_source[source_value] = count
        
        # By priority
        by_priority = {}
        for priority_value, priority_label in Lead.Priority.choices:
            count = queryset.filter(priority=priority_value).count()
            if count > 0:
                by_priority[priority_value] = count
        
        # Conversion rate
        converted_count = by_status.get("converted", 0)
        conversion_rate = (converted_count / total * 100) if total > 0 else 0.0
        
        # Average score
        avg_score = queryset.aggregate(avg=Avg("score"))["avg"] or 0.0
        
        # Total estimated value
        total_value = queryset.aggregate(total=Sum("estimated_value"))["total"] or Decimal("0")
        
        # Recent count (last 30 days)
        recent_date = datetime.now() - timedelta(days=30)
        recent_count = queryset.filter(created_at__gte=recent_date).count()
        
        return Response({
            "total": total,
            "by_status": by_status,
            "by_source": by_source,
            "by_priority": by_priority,
            "conversion_rate": round(conversion_rate, 2),
            "average_score": round(avg_score, 2),
            "total_estimated_value": float(total_value),
            "recent_count": recent_count,
        })
    
    @extend_schema(
        summary="Get lead activities",
        description="Get a paginated list of activities for a lead.",
        responses={200: {"type": "object"}},
    )
    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        """Get lead activities"""
        from apps.activities.models import Activity
        from apps.activities.serializers import ActivitySerializer
        from rest_framework.pagination import PageNumberPagination
        
        lead = self.get_object()
        activities = Activity.objects.filter(lead=lead).select_related("created_by").order_by("-occurred_at")
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get("page_size", 10)
        page = paginator.paginate_queryset(activities, request)
        
        if page is not None:
            serializer = ActivitySerializer(page, many=True, context=self.get_serializer_context())
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ActivitySerializer(activities, many=True, context=self.get_serializer_context())
        return Response({"data": serializer.data})

