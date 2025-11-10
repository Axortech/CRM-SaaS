from django_filters.rest_framework import FilterSet, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.notifications.models import AuditLogEntry, Notification
from apps.notifications.serializers import AuditLogSerializer, NotificationSerializer


class NotificationFilterSet(FilterSet):
    is_read = filters.BooleanFilter(field_name="is_read")
    user = filters.UUIDFilter(field_name="user_id")

    class Meta:
        model = Notification
        fields = ["is_read", "user", "notification_type"]


class NotificationViewSet(OrganizationScopedViewSet):
    schema_tags = ["Notifications"]
    queryset = Notification.objects.select_related("user")
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilterSet
    search_fields = ["title", "message"]
    ordering_fields = ["created_at"]

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = request.data.get("read_at")
        notification.save()
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        queryset = self.filter_queryset(self.get_queryset()).filter(user=request.user)
        queryset.update(is_read=True)
        return Response({"updated": queryset.count()}, status=status.HTTP_200_OK)


class AuditLogFilterSet(FilterSet):
    action = filters.CharFilter(field_name="action")
    entity_type = filters.CharFilter(field_name="entity_type")

    class Meta:
        model = AuditLogEntry
        fields = ["action", "entity_type", "user"]


class AuditLogViewSet(OrganizationScopedViewSet):
    schema_tags = ["Notifications"]
    queryset = AuditLogEntry.objects.select_related("user")
    serializer_class = AuditLogSerializer
    filterset_class = AuditLogFilterSet
    search_fields = ["entity_type", "entity_id", "changes"]
    ordering_fields = ["timestamp"]

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
