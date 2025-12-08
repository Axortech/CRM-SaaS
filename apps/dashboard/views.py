from datetime import datetime, timedelta

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.dashboard.models import DashboardWidget
from apps.dashboard.serializers import DashboardWidgetSerializer
from apps.contacts.models import Contact
from apps.contacts.serializers import ContactSerializer
from django.db.models import Sum
from apps.leads.models import Lead
from apps.leads.serializers import LeadSerializer


class DashboardMetricsViewSet(OrganizationScopedViewSet):
    """
    ViewSet for dashboard statistics and metrics.
    
    Provides aggregated data for the organization dashboard.
    """
    schema_tags = ["Dashboard"]
    http_method_names = ["get"]
    queryset = DashboardWidget.objects.none()
    serializer_class = DashboardWidgetSerializer

    @extend_schema(
        summary="Get dashboard statistics",
        description="Get comprehensive dashboard statistics including contacts, leads, and recent items.",
        responses={200: {"type": "object"}},
    )
    def list(self, request, *args, **kwargs):
        """Get dashboard statistics"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Contact statistics
        contacts_queryset = Contact.objects.filter(organization=organization)
        contacts_total = contacts_queryset.count()
        contacts_active = contacts_queryset.filter(stage=Contact.Stage.CUSTOMER).count()
        contacts_inactive = contacts_queryset.filter(stage=Contact.Stage.INACTIVE).count()
        
        # Recent contacts (last 30 days)
        recent_date = datetime.now() - timedelta(days=30)
        contacts_recent = contacts_queryset.filter(created_at__gte=recent_date).count()
        
        # Recent contacts list (last 5)
        recent_contacts_list = contacts_queryset.order_by("-created_at")[:5]
        recent_contacts_serializer = ContactSerializer(recent_contacts_list, many=True, context={"organization": organization})
        
        # Lead statistics
        leads_queryset = Lead.objects.filter(organization=organization)
        leads_total = leads_queryset.count()
        leads_qualified = leads_queryset.filter(status=Lead.Status.QUALIFIED).count()
        
        # Conversion rate
        leads_converted = leads_queryset.filter(status=Lead.Status.CONVERTED).count()
        conversion_rate = (leads_converted / leads_total * 100) if leads_total > 0 else 0.0
        
        # Total estimated value
        from decimal import Decimal
        total_estimated_value = leads_queryset.aggregate(
            total=Sum("estimated_value")
        )["total"] or Decimal("0")
        
        # Recent leads (last 5)
        recent_leads_list = leads_queryset.order_by("-created_at")[:5]
        recent_leads_serializer = LeadSerializer(recent_leads_list, many=True, context={"organization": organization})
        
        return Response({
            "contacts": {
                "total": contacts_total,
                "active": contacts_active,
                "inactive": contacts_inactive,
                "recent_count": contacts_recent,
            },
            "leads": {
                "total": leads_total,
                "qualified": leads_qualified,
                "conversion_rate": round(conversion_rate, 2),
                "total_estimated_value": float(total_estimated_value),
            },
            "recent_contacts": recent_contacts_serializer.data,
            "recent_leads": recent_leads_serializer.data,
        })


class DashboardWidgetViewSet(OrganizationScopedViewSet):
    schema_tags = ["Dashboard"]
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    search_fields = ["title", "widget_type"]
    ordering_fields = ["order", "created_at"]
