from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.companies.models import Company

User = get_user_model()


class CompanySerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )
    parent_company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Company
        fields = [
            "id",
            "organization",
            "name",
            "website",
            "industry",
            "employee_count",
            "annual_revenue",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "postal_code",
            "phone",
            "parent_company",
            "owner",
            "custom_fields",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]

    def _get_organization(self):
        return (
            self.context.get("organization")
            or getattr(self.instance, "organization", None)
        )

    def validate_parent_company(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and value.organization_id != organization.id:
            raise serializers.ValidationError("Parent company must belong to the same organization.")
        return value

    def validate_owner(self, value):
        if not value:
            return value
        organization = self._get_organization()
        if organization and not organization.members.filter(user=value, is_active=True).exists() and organization.owner_id != value.id:
            raise serializers.ValidationError("Owner must be part of the organization.")
        return value
