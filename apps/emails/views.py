from django_filters.rest_framework import FilterSet, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.emails.models import Email, EmailCampaign, EmailTemplate
from apps.emails.serializers import (
    EmailCampaignSerializer,
    EmailSendSerializer,
    EmailSerializer,
    EmailTemplateSerializer,
)


class EmailTemplateFilterSet(FilterSet):
    is_active = filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = EmailTemplate
        fields = ["is_active", "name"]


class EmailFilterSet(FilterSet):
    contact = filters.UUIDFilter(field_name="contact_id")
    is_sent = filters.BooleanFilter(field_name="is_sent")

    class Meta:
        model = Email
        fields = ["contact", "is_sent"]


class EmailTemplateViewSet(OrganizationScopedViewSet):
    schema_tags = ["Emails"]
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    filterset_class = EmailTemplateFilterSet
    search_fields = ["name", "subject"]
    ordering_fields = ["name", "created_at", "updated_at"]


class EmailViewSet(OrganizationScopedViewSet):
    schema_tags = ["Emails"]
    queryset = Email.objects.select_related("contact", "template")
    serializer_class = EmailSerializer
    filterset_class = EmailFilterSet
    search_fields = ["subject", "body", "to_emails"]
    ordering_fields = ["created_at", "updated_at", "sent_at"]

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        email = self.get_object()
        if email.is_sent:
            return Response({"detail": "Email already sent."}, status=status.HTTP_400_BAD_REQUEST)
        email.is_sent = True
        email.sent_at = request.data.get("sent_at")
        email.save()
        return Response(self.get_serializer(email).data)

    @action(detail=False, methods=["post"], url_path="send")
    def send_new(self, request):
        serializer = EmailSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = self._get_request_organization()
        email = Email.objects.create(
            organization=organization,
            subject=serializer.validated_data["subject"],
            body=serializer.validated_data["body"],
            from_email=request.user.email,
            to_emails=serializer.validated_data["to_emails"],
            cc_emails=serializer.validated_data.get("cc_emails", []),
            bcc_emails=serializer.validated_data.get("bcc_emails", []),
            is_sent=True,
            sent_at=request.data.get("sent_at"),
            created_by=request.user,
        )
        return Response(self.get_serializer(email).data, status=status.HTTP_201_CREATED)


class EmailCampaignViewSet(OrganizationScopedViewSet):
    schema_tags = ["Emails"]
    queryset = EmailCampaign.objects.all()
    serializer_class = EmailCampaignSerializer
    search_fields = ["name", "subject"]
    ordering_fields = ["created_at", "updated_at"]

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        campaign = self.get_object()
        return Response(campaign.stats or {})
