from rest_framework import serializers

from apps.activities.models import Activity
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.models import Lead
from apps.opportunities.models import Opportunity


class ActivitySerializer(serializers.ModelSerializer):
    entity_type = serializers.SerializerMethodField()
    entity_id = serializers.SerializerMethodField()
    type = serializers.CharField(source="activity_type", read_only=True)
    title = serializers.CharField(source="subject", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    opportunity = serializers.PrimaryKeyRelatedField(
        queryset=Opportunity.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    lead = serializers.PrimaryKeyRelatedField(
        queryset=Lead.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Activity
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "type",
            "title",
            "description",
            "metadata",
            "created_by",
            "created_by_name",
            "created_at",
            # Write-only fields for creating activities
            "contact",
            "lead",
            "company",
            "opportunity",
            "activity_type",
            "subject",
            "occurred_at",
            "duration",
        ]
        read_only_fields = [
            "id",
            "entity_type",
            "entity_id",
            "type",
            "title",
            "created_by",
            "created_by_name",
            "created_at",
        ]
    
    def get_entity_type(self, obj):
        """Get entity type"""
        return obj.entity_type
    
    def get_entity_id(self, obj):
        """Get entity ID"""
        return obj.entity_id
    
    def get_created_by_name(self, obj):
        """Get creator's name"""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

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
    
    def validate_lead(self, value):
        return self._validate_relation(value, "Lead must belong to the organization.")
    
    def validate(self, attrs):
        """Validate that at least one entity is provided"""
        entity_fields = ["contact", "lead", "company", "opportunity"]
        has_entity = any(attrs.get(field) for field in entity_fields)
        
        if not has_entity and not self.instance:
            raise serializers.ValidationError("At least one entity (contact, lead, company, or opportunity) must be provided.")
        
        return attrs
    
    def create(self, validated_data):
        """Create activity with proper entity mapping"""
        # Map subject to title if provided in request
        if "title" in self.initial_data:
            validated_data["subject"] = self.initial_data["title"]
        elif "subject" not in validated_data:
            validated_data["subject"] = validated_data.get("description", "")[:255] or "Activity"
        
        # Map type to activity_type if provided
        if "type" in self.initial_data:
            validated_data["activity_type"] = self.initial_data["type"]
        
        # Set occurred_at to now if not provided
        if "occurred_at" not in validated_data:
            from django.utils import timezone
            validated_data["occurred_at"] = timezone.now()
        
        return super().create(validated_data)
