from rest_framework import serializers

from apps.contacts.models import Contact
from apps.emails.models import Email, EmailCampaign, EmailTemplate


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = [
            "id",
            "organization",
            "name",
            "subject",
            "body_html",
            "body_text",
            "variables",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]


class EmailSerializer(serializers.ModelSerializer):
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        allow_null=True,
        required=False,
    )
    template = serializers.PrimaryKeyRelatedField(
        queryset=EmailTemplate.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Email
        fields = [
            "id",
            "organization",
            "contact",
            "subject",
            "body",
            "from_email",
            "to_emails",
            "cc_emails",
            "bcc_emails",
            "is_sent",
            "sent_at",
            "is_opened",
            "opened_at",
            "click_count",
            "template",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "is_sent",
            "sent_at",
            "is_opened",
            "opened_at",
            "click_count",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def _get_organization(self):
        return (
            self.context.get("organization")
            or getattr(self.instance, "organization", None)
        )

    def _validate_relation(self, value, message):
        if not value:
            return value
        organization = self._get_organization()
        if organization and value.organization_id != organization.id:
            raise serializers.ValidationError(message)
        return value

    def validate_contact(self, value):
        return self._validate_relation(value, "Contact must belong to the same organization.")

    def validate_template(self, value):
        return self._validate_relation(value, "Template must belong to the same organization.")


class EmailSendSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    to_emails = serializers.ListField(child=serializers.EmailField(), allow_empty=False)
    cc_emails = serializers.ListField(child=serializers.EmailField(), required=False)
    bcc_emails = serializers.ListField(child=serializers.EmailField(), required=False)


class EmailCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailCampaign
        fields = [
            "id",
            "organization",
            "name",
            "subject",
            "body",
            "recipients",
            "stats",
            "is_sent",
            "sent_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "stats",
            "is_sent",
            "sent_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
