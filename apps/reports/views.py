from django_filters.rest_framework import FilterSet, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.reports.models import Report, ScheduledReport
from apps.reports.serializers import (
    ReportExecuteSerializer,
    ReportExportSerializer,
    ReportSerializer,
    ScheduledReportSerializer,
)


class ReportFilterSet(FilterSet):
    report_type = filters.CharFilter(field_name="report_type")
    is_shared = filters.BooleanFilter(field_name="is_shared")

    class Meta:
        model = Report
        fields = ["report_type", "is_shared"]


class ReportViewSet(OrganizationScopedViewSet):
    schema_tags = ["Reports"]
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    filterset_class = ReportFilterSet
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        report = self.get_object()
        serializer = ReportExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Placeholder for actual execution logic
        return Response(
            {
                "report_id": str(report.id),
                "status": "queued",
                "parameters": serializer.validated_data.get("parameters"),
            }
        )

    @action(detail=True, methods=["get"], url_path="data")
    def data(self, request, pk=None):
        report = self.get_object()
        return Response({"report_id": str(report.id), "data": []})

    @action(detail=True, methods=["post"], url_path="export")
    def export(self, request, pk=None):
        serializer = ReportExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "report_id": pk,
                "format": serializer.validated_data["format"],
                "status": "export_queued",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="schedule")
    def schedule(self, request, pk=None):
        report = self.get_object()
        serializer = ScheduledReportSerializer(data=request.data, context={"organization": report.organization})
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save(report=report, organization=report.organization, created_by=request.user)
        return Response(ScheduledReportSerializer(schedule).data, status=status.HTTP_201_CREATED)


class ScheduledReportViewSet(OrganizationScopedViewSet):
    schema_tags = ["Reports"]
    queryset = ScheduledReport.objects.select_related("report")
    serializer_class = ScheduledReportSerializer
    search_fields = ["report__name"]
    ordering_fields = ["created_at", "next_run_at"]
