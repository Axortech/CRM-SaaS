from django_filters.rest_framework import FilterSet, filters

from core.viewsets import OrganizationScopedViewSet
from apps.activities.models import Activity
from apps.activities.serializers import ActivitySerializer


class ActivityFilterSet(FilterSet):
    activity_type = filters.CharFilter(field_name="activity_type")
    contact = filters.UUIDFilter(field_name="contact_id")
    company = filters.UUIDFilter(field_name="company_id")
    opportunity = filters.UUIDFilter(field_name="opportunity_id")
    occurred_before = filters.DateTimeFilter(field_name="occurred_at", lookup_expr="lte")
    occurred_after = filters.DateTimeFilter(field_name="occurred_at", lookup_expr="gte")

    class Meta:
        model = Activity
        fields = ["activity_type", "contact", "company", "opportunity"]


class ActivityViewSet(OrganizationScopedViewSet):
    schema_tags = ["Activities"]
    queryset = Activity.objects.select_related("contact", "company", "opportunity", "created_by")
    serializer_class = ActivitySerializer
    filterset_class = ActivityFilterSet
    search_fields = ["subject", "description"]
    ordering_fields = ["occurred_at", "created_at"]
