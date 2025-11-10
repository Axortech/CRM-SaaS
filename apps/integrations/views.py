from django_filters.rest_framework import FilterSet, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.integrations.models import IntegrationKey, Webhook
from apps.integrations.serializers import IntegrationKeySerializer, WebhookSerializer


class WebhookFilterSet(FilterSet):
    is_active = filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Webhook
        fields = ["is_active"]


class WebhookViewSet(OrganizationScopedViewSet):
    schema_tags = ["Integrations"]
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    filterset_class = WebhookFilterSet
    search_fields = ["name", "url"]
    ordering_fields = ["name", "created_at"]


class IntegrationKeyFilterSet(FilterSet):
    is_active = filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = IntegrationKey
        fields = ["is_active"]


class IntegrationKeyViewSet(OrganizationScopedViewSet):
    schema_tags = ["Integrations"]
    queryset = IntegrationKey.objects.all()
    serializer_class = IntegrationKeySerializer
    filterset_class = IntegrationKeyFilterSet
    search_fields = ["name", "key"]
    ordering_fields = ["created_at", "updated_at"]
