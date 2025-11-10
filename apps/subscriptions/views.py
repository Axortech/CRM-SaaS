from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from apps.organizations import services as org_services
from apps.organizations.models import Organization
from apps.subscriptions.constants import PLAN_DEFINITIONS
from apps.subscriptions.models import Payment, PaymentMethod, Subscription
from apps.subscriptions.serializers import (
    PaymentCreateSerializer,
    PaymentMethodSerializer,
    PaymentSerializer,
    PlanSerializer,
    SubscriptionChangePlanSerializer,
    SubscriptionCreateSerializer,
    SubscriptionSerializer,
    SubscriptionUpdateSerializer,
)
from apps.subscriptions import services as subscription_services


class PlanListView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(tags=["Subscriptions"])
    def get(self, request, *args, **kwargs):
        serializer = PlanSerializer(PLAN_DEFINITIONS, many=True)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet):
    schema_tags = ["Subscriptions"]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Subscription.objects.all()

    def get_queryset(self):
        user = self.request.user
        return (
            Subscription.objects.filter(
                Q(organization__owner=user)
                | Q(
                    organization__members__user=user,
                    organization__members__is_active=True,
                )
            )
            .distinct()
            .order_by("organization__name")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return SubscriptionCreateSerializer
        if self.action in ["update", "partial_update"]:
            return SubscriptionUpdateSerializer
        return SubscriptionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        output_serializer = SubscriptionSerializer(
            subscription, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()
        output_serializer = SubscriptionSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(output_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        subscription = serializer.instance
        self._ensure_admin(subscription.organization, self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_admin(instance.organization, self.request.user)
        instance.delete()

    def _ensure_admin(self, organization: Organization, user):
        if not org_services.user_is_org_admin(user, organization):
            raise PermissionDenied("Administrator access required.")

    @action(detail=True, methods=["post"])
    def upgrade(self, request, pk=None):
        subscription = self.get_object()
        self._ensure_admin(subscription.organization, request.user)
        serializer = SubscriptionChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        start, end = subscription_services.calculate_billing_period_end(data["billing_cycle"])
        plan_definition = subscription_services.get_plan_definition(data["plan"])
        subscription.plan = data["plan"]
        subscription.billing_cycle = data["billing_cycle"]
        subscription.status = Subscription.Status.ACTIVE
        subscription.current_period_start = start
        subscription.current_period_end = end
        subscription.user_limit = plan_definition["user_limit"]
        subscription.save()
        return Response(SubscriptionSerializer(subscription).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        self._ensure_admin(subscription.organization, request.user)
        subscription.status = Subscription.Status.CANCELED
        subscription.current_period_end = timezone.now().date()
        subscription.save()
        return Response(SubscriptionSerializer(subscription).data)

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        subscription = self.get_object()
        self._ensure_admin(subscription.organization, request.user)
        subscription.status = Subscription.Status.ACTIVE
        start, end = subscription_services.calculate_billing_period_end(subscription.billing_cycle)
        subscription.current_period_start = start
        subscription.current_period_end = end
        subscription.save()
        return Response(SubscriptionSerializer(subscription).data)

    @action(detail=True, methods=["get", "post"], url_path="payments")
    def payments(self, request, pk=None):
        subscription = self.get_object()
        if request.method == "GET":
            payments = subscription.payments.all().order_by("-created_at")
            serializer = PaymentSerializer(payments, many=True)
            return Response(serializer.data)

        self._ensure_admin(subscription.organization, request.user)
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = Payment.objects.create(
            subscription=subscription,
            status=Payment.Status.PENDING,
            **serializer.validated_data,
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="payments/(?P<payment_id>[^/.]+)/mark-paid")
    def mark_payment_paid(self, request, pk=None, payment_id=None):
        subscription = self.get_object()
        self._ensure_admin(subscription.organization, request.user)
        try:
            payment = subscription.payments.get(pk=payment_id)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        payment.mark_paid()
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["get"], url_path="invoices")
    def invoices(self, request, pk=None):
        subscription = self.get_object()
        invoices = subscription.payments.order_by("-created_at")
        return Response(PaymentSerializer(invoices, many=True).data)

    @action(detail=True, methods=["get", "post"], url_path="payment-methods")
    def payment_methods(self, request, pk=None):
        subscription = self.get_object()
        if request.method == "GET":
            methods = subscription.payment_methods.all()
            return Response(PaymentMethodSerializer(methods, many=True).data)

        self._ensure_admin(subscription.organization, request.user)
        serializer = PaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = PaymentMethod.objects.create(subscription=subscription, **serializer.validated_data)
        if method.is_default:
            subscription.payment_methods.exclude(pk=method.pk).update(is_default=False)
        return Response(PaymentMethodSerializer(method).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path="payment-methods/(?P<method_id>[^/.]+)")
    def delete_payment_method(self, request, pk=None, method_id=None):
        subscription = self.get_object()
        self._ensure_admin(subscription.organization, request.user)
        try:
            method = subscription.payment_methods.get(pk=method_id)
        except PaymentMethod.DoesNotExist:
            return Response({"detail": "Payment method not found."}, status=status.HTTP_404_NOT_FOUND)
        method.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
