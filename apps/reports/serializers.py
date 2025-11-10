from rest_framework import serializers

from apps.reports.models import Report, ScheduledReport


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "report_type",
            "configuration",
            "is_shared",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]


class ScheduledReportSerializer(serializers.ModelSerializer):
    report = serializers.PrimaryKeyRelatedField(queryset=Report.objects.all())

    class Meta:
        model = ScheduledReport
        fields = [
            "id",
            "report",
            "schedule",
            "recipients",
            "next_run_at",
            "last_run_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "next_run_at", "last_run_at", "created_at", "updated_at"]

    def _get_organization(self):
        return self.context.get("organization")

    def validate_report(self, value):
        organization = self._get_organization()
        if organization and value.organization_id != organization.id:
            raise serializers.ValidationError("Report must belong to the same organization.")
        return value


class ReportExecuteSerializer(serializers.Serializer):
    parameters = serializers.DictField(required=False)


class ReportExportSerializer(serializers.Serializer):
    format = serializers.ChoiceField(choices=[("pdf", "PDF"), ("csv", "CSV"), ("xlsx", "Excel")])
