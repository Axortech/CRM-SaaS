from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.dashboard.models import DashboardWidget
from apps.dashboard.serializers import DashboardWidgetSerializer
from apps.contacts.models import Contact
from apps.opportunities.models import Opportunity
from apps.tasks.models import Task


class DashboardMetricsViewSet(OrganizationScopedViewSet):
    schema_tags = ["Dashboard"]
    http_method_names = ["get"]
    queryset = DashboardWidget.objects.none()
    serializer_class = DashboardWidgetSerializer

    def list(self, request, *args, **kwargs):
        organization = self._get_request_organization()
        contacts = Contact.objects.filter(organization=organization).count()
        opportunities = Opportunity.objects.filter(organization=organization).count()
        tasks_open = Task.objects.filter(
            organization=organization,
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS],
        ).count()
        return Response(
            {
                "contacts": contacts,
                "opportunities": opportunities,
                "tasks_open": tasks_open,
            }
        )


class DashboardWidgetViewSet(OrganizationScopedViewSet):
    schema_tags = ["Dashboard"]
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer
    search_fields = ["title", "widget_type"]
    ordering_fields = ["order", "created_at"]
