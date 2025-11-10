from django_filters.rest_framework import FilterSet, filters

from core.viewsets import OrganizationScopedViewSet
from apps.customization.models import CustomField, LayoutConfiguration
from apps.customization.serializers import CustomFieldSerializer, LayoutConfigurationSerializer


class CustomFieldFilterSet(FilterSet):
    entity_type = filters.CharFilter(field_name="entity_type")
    is_active = filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = CustomField
        fields = ["entity_type", "is_active"]


class CustomFieldViewSet(OrganizationScopedViewSet):
    schema_tags = ["Customization"]
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer
    filterset_class = CustomFieldFilterSet
    search_fields = ["field_label", "field_name"]
    ordering_fields = ["order", "created_at", "updated_at"]


class LayoutConfigurationFilterSet(FilterSet):
    page_type = filters.CharFilter(field_name="page_type")
    user = filters.UUIDFilter(field_name="user_id")

    class Meta:
        model = LayoutConfiguration
        fields = ["page_type", "user", "is_default"]


class LayoutConfigurationViewSet(OrganizationScopedViewSet):
    schema_tags = ["Customization"]
    queryset = LayoutConfiguration.objects.select_related("user")
    serializer_class = LayoutConfigurationSerializer
    filterset_class = LayoutConfigurationFilterSet
    search_fields = ["page_type"]
    ordering_fields = ["created_at", "updated_at"]
