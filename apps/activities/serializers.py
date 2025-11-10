from rest_framework import serializers

from apps.activities.models import Activity
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.opportunities.models import Opportunity


class ActivitySerializer(serializers.ModelSerializer):
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        allow_null=True,
        required=False,
    )
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        allow_null=True,
        required=False,
    )
    opportunity = serializers.PrimaryKeyRelatedField(
        queryset=Opportunity.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Activity
        fields = [
            "id",
            "organization",
            "activity_type",
            "subject",
            "description",
            "duration",
            "occurred_at",
            "contact",
            "company",
            "opportunity",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]

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
        return self._validate_relation(value, "Contact must belong to the organization.")

    def validate_company(self, value):
        return self._validate_relation(value, "Company must belong to the organization.")

    def validate_opportunity(self, value):
        return self._validate_relation(value, "Opportunity must belong to the organization.")
