from datetime import date, timedelta

from django.db.models import Sum, Count
from django.utils import timezone
from django_filters.rest_framework import FilterSet, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.opportunities.models import Opportunity, OpportunityLineItem, OpportunityStage
from apps.opportunities.serializers import (
    OpportunityStageSerializer,
    OpportunityStageReorderSerializer,
    OpportunityForecastSerializer,
    OpportunityLineItemSerializer,
    OpportunityPipelineSerializer,
    OpportunitySerializer,
)


class OpportunityFilterSet(FilterSet):
    stage = filters.UUIDFilter(field_name="stage_id")
    status = filters.CharFilter(field_name="status")
    owner = filters.UUIDFilter(field_name="owner_id")
    company = filters.UUIDFilter(field_name="company_id")

    class Meta:
        model = Opportunity
        fields = ["stage", "status", "owner", "company"]


class OpportunityViewSet(OrganizationScopedViewSet):
    schema_tags = ["Opportunities"]
    queryset = Opportunity.objects.select_related(
        "company", "contact", "owner", "stage"
    ).prefetch_related("line_items")
    serializer_class = OpportunitySerializer
    filterset_class = OpportunityFilterSet
    search_fields = ["name", "company__name", "contact__first_name", "contact__last_name"]
    ordering_fields = ["expected_close_date", "amount", "created_at", "updated_at"]

    @action(detail=True, methods=["post"])
    def mark_won(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.status = Opportunity.Status.WON
        opportunity.actual_close_date = request.data.get("actual_close_date") or timezone.now().date()
        opportunity.save()
        return Response(self.get_serializer(opportunity).data)

    @action(detail=True, methods=["post"])
    def mark_lost(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.status = Opportunity.Status.LOST
        opportunity.loss_reason = request.data.get("loss_reason", "")
        opportunity.actual_close_date = request.data.get("actual_close_date") or timezone.now().date()
        opportunity.save()
        return Response(self.get_serializer(opportunity).data)

    @action(detail=True, methods=["post"])
    def move_stage(self, request, pk=None):
        opportunity = self.get_object()
        stage_id = request.data.get("stage")
        if not stage_id:
            return Response({"detail": "stage is required."}, status=400)
        try:
            stage = OpportunityStage.objects.get(id=stage_id)
        except OpportunityStage.DoesNotExist:
            return Response({"detail": "Stage not found."}, status=status.HTTP_404_NOT_FOUND)
        if stage.organization_id != opportunity.organization_id:
            return Response({"detail": "Stage must belong to the same organization."}, status=status.HTTP_400_BAD_REQUEST)
        opportunity.stage = stage
        opportunity.save()
        return Response(self.get_serializer(opportunity).data)

    @action(detail=True, methods=["post"], url_path="line-items")
    def add_line_item(self, request, pk=None):
        opportunity = self.get_object()
        serializer = OpportunityLineItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        line_item = OpportunityLineItem.objects.create(opportunity=opportunity, **serializer.validated_data)
        return Response(OpportunityLineItemSerializer(line_item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="line-items/(?P<item_id>[^/.]+)")
    def update_line_item(self, request, pk=None, item_id=None):
        opportunity = self.get_object()
        try:
            line_item = opportunity.line_items.get(pk=item_id)
        except OpportunityLineItem.DoesNotExist:
            return Response({"detail": "Line item not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OpportunityLineItemSerializer(line_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["delete"], url_path="line-items/(?P<item_id>[^/.]+)")
    def delete_line_item(self, request, pk=None, item_id=None):
        opportunity = self.get_object()
        try:
            line_item = opportunity.line_items.get(pk=item_id)
        except OpportunityLineItem.DoesNotExist:
            return Response({"detail": "Line item not found."}, status=status.HTTP_404_NOT_FOUND)
        line_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="pipeline")
    def pipeline(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        pipeline_data = queryset.values("stage__name").annotate(
            total_amount=Sum("amount"),
            opportunity_count=Count("id"),
        )
        result = [
            {
                "stage": record["stage__name"],
                "total_amount": record["total_amount"] or 0,
                "opportunity_count": record["opportunity_count"] or 0,
            }
            for record in pipeline_data
        ]
        serializer = OpportunityPipelineSerializer(result, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="forecast")
    def forecast(self, request):
        queryset = self.filter_queryset(self.get_queryset()).filter(
            status=Opportunity.Status.OPEN,
            expected_close_date__isnull=False,
        )
        today = date.today()
        periods = {
            "this_month": (today.replace(day=1), today.replace(day=28) + timedelta(days=4)),
            "next_month": (
                (today.replace(day=28) + timedelta(days=4)).replace(day=1),
                (today.replace(day=28) + timedelta(days=4)).replace(day=28) + timedelta(days=4),
            ),
        }
        results = []
        for label, (start, end) in periods.items():
            period_qs = queryset.filter(expected_close_date__range=(start, end))
            total = period_qs.aggregate(total_amount=Sum("amount"))["total_amount"] or 0
            results.append({"period": label, "total_amount": total})
        serializer = OpportunityForecastSerializer(results, many=True)
        return Response(serializer.data)


class OpportunityStageViewSet(OrganizationScopedViewSet):
    schema_tags = ["Opportunities"]
    queryset = OpportunityStage.objects.all()
    serializer_class = OpportunityStageSerializer
    search_fields = ["name"]
    ordering_fields = ["order", "created_at"]

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        serializer = OpportunityStageReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stage_ids = serializer.validated_data["stage_ids"]
        stages = list(self.get_queryset().filter(id__in=stage_ids))
        stage_map = {stage.id: stage for stage in stages}
        order = 0
        for stage_id in stage_ids:
            stage = stage_map.get(stage_id)
            if stage:
                stage.order = order
                stage.save(update_fields=["order"])
                order += 1
        return Response({"detail": "Stages reordered."})
