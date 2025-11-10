from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.opportunities.models import Opportunity, OpportunityLineItem, OpportunityStage

User = get_user_model()


class OpportunityStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityStage
        fields = [
            "id",
            "organization",
            "name",
            "order",
            "probability",
            "is_closed_stage",
            "is_won_stage",
            "color",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class OpportunityStageReorderSerializer(serializers.Serializer):
    stage_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)


class OpportunityLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityLineItem
        fields = [
            "id",
            "product_name",
            "description",
            "quantity",
            "unit_price",
            "discount_percent",
            "total_price",
        ]
        read_only_fields = ["id"]


class OpportunityPipelineSerializer(serializers.Serializer):
    stage = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    opportunity_count = serializers.IntegerField()


class OpportunityForecastSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)


class OpportunitySerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        allow_null=True,
        required=False,
    )
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        allow_null=True,
        required=False,
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )
    stage = serializers.PrimaryKeyRelatedField(
        queryset=OpportunityStage.objects.all(),
        allow_null=True,
        required=False,
    )
    line_items = OpportunityLineItemSerializer(many=True, required=False)

    class Meta:
        model = Opportunity
        fields = [
            "id",
            "organization",
            "name",
            "company",
            "contact",
            "stage",
            "amount",
            "currency",
            "probability",
            "expected_close_date",
            "actual_close_date",
            "status",
            "loss_reason",
            "source",
            "owner",
            "custom_fields",
            "line_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]

    def _get_organization(self):
        return (
            self.context.get("organization")
            or getattr(self.instance, "organization", None)
        )

    def validate_stage(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and value.organization_id != organization.id:
            raise serializers.ValidationError("Stage must belong to the same organization.")
        return value

    def validate_company(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and value.organization_id != organization.id:
            raise serializers.ValidationError("Company must belong to the same organization.")
        return value

    def validate_contact(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and value.organization_id != organization.id:
            raise serializers.ValidationError("Contact must belong to the same organization.")
        return value

    def validate_owner(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and not organization.members.filter(user=value, is_active=True).exists() and organization.owner_id != value.id:
            raise serializers.ValidationError("Owner must belong to the organization.")
        return value

    def create(self, validated_data):
        line_items = validated_data.pop("line_items", [])
        opportunity = super().create(validated_data)
        self._save_line_items(opportunity, line_items)
        return opportunity

    def update(self, instance, validated_data):
        line_items = validated_data.pop("line_items", None)
        opportunity = super().update(instance, validated_data)
        if line_items is not None:
            opportunity.line_items.all().delete()
            self._save_line_items(opportunity, line_items)
        return opportunity

    def _save_line_items(self, opportunity, line_items):
        for item in line_items:
            OpportunityLineItem.objects.create(opportunity=opportunity, **item)
