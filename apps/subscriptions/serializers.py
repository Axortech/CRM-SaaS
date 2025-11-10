from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.organizations import services as org_services
from apps.organizations.models import Organization
from apps.subscriptions.constants import PLAN_DEFINITIONS
from apps.subscriptions.models import Payment, PaymentMethod, Subscription
from apps.subscriptions import services as subscription_services


class PlanSerializer(serializers.Serializer):
    plan = serializers.CharField()
    name = serializers.CharField()
    price_monthly = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    user_limit = serializers.IntegerField()
    features = serializers.ListField(child=serializers.CharField())


class SubscriptionSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "organization",
            "organization_name",
            "plan",
            "billing_cycle",
            "status",
            "trial_end_date",
            "current_period_start",
            "current_period_end",
            "stripe_subscription_id",
            "stripe_customer_id",
            "user_limit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "trial_end_date",
            "current_period_start",
            "current_period_end",
            "stripe_subscription_id",
            "stripe_customer_id",
            "user_limit",
            "created_at",
            "updated_at",
        ]


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    organization = serializers.UUIDField(write_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "organization", "plan", "billing_cycle"]
        read_only_fields = ["id"]

    def validate_plan(self, value):
        if value not in Subscription.Plan.values:
            raise serializers.ValidationError("Invalid plan.")
        return value

    def validate_billing_cycle(self, value):
        if value not in Subscription.BillingCycle.values:
            raise serializers.ValidationError("Invalid billing cycle.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        org_id = attrs["organization"]
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Organization not found.")

        if not org_services.user_is_org_admin(request.user, organization):
            raise serializers.ValidationError("You do not have permission for this organization.")

        attrs["organization"] = organization
        attrs["status"] = Subscription.Status.ACTIVE
        start, end = subscription_services.calculate_billing_period_end(attrs["billing_cycle"])
        attrs["current_period_start"] = start
        attrs["current_period_end"] = end
        attrs["trial_end_date"] = timezone.now().date() + timedelta(days=14)
        plan_definition = subscription_services.get_plan_definition(attrs["plan"])
        attrs["user_limit"] = plan_definition["user_limit"]
        return attrs


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["billing_cycle"]


class SubscriptionChangePlanSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=Subscription.Plan.choices)
    billing_cycle = serializers.ChoiceField(choices=Subscription.BillingCycle.choices)


class PaymentSerializer(serializers.ModelSerializer):
    subscription_plan = serializers.CharField(source="subscription.plan", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "subscription",
            "subscription_plan",
            "amount",
            "currency",
            "status",
            "stripe_payment_intent_id",
            "invoice_number",
            "invoice_pdf_url",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "paid_at", "created_at", "updated_at"]


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "currency",
            "stripe_payment_intent_id",
            "invoice_number",
            "invoice_pdf_url",
        ]
        read_only_fields = ["id"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "method_type",
            "brand",
            "last4",
            "exp_month",
            "exp_year",
            "is_default",
            "external_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
