from django.utils import timezone
from django_filters.rest_framework import FilterSet, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer


class TaskFilterSet(FilterSet):
    status = filters.CharFilter(field_name="status")
    priority = filters.CharFilter(field_name="priority")
    assigned_to = filters.UUIDFilter(field_name="assigned_to_id")
    due_before = filters.DateTimeFilter(field_name="due_date", lookup_expr="lte")
    due_after = filters.DateTimeFilter(field_name="due_date", lookup_expr="gte")

    class Meta:
        model = Task
        fields = ["status", "priority", "assigned_to"]


class TaskViewSet(OrganizationScopedViewSet):
    schema_tags = ["Tasks"]
    queryset = Task.objects.select_related("assigned_to", "contact", "company", "opportunity")
    serializer_class = TaskSerializer
    filterset_class = TaskFilterSet
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "created_at", "updated_at"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = Task.Status.COMPLETED
        task.completed_at = request.data.get("completed_at") or timezone.now()
        task.save()
        return Response(self.get_serializer(task).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="calendar")
    def calendar(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if start and end:
            queryset = queryset.filter(due_date__range=(start, end))
        events = [
            {
                "id": str(task.id),
                "title": task.title,
                "due_date": task.due_date,
                "status": task.status,
            }
            for task in queryset
        ]
        return Response(events)

    @action(detail=False, methods=["get"], url_path="my-tasks")
    def my_tasks(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(assigned_to=request.user)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
