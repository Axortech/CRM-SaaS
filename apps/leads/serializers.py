from rest_framework import serializers

from apps.contacts.models import Tag
from apps.contacts.serializers import ContactSerializer
from apps.leads.models import Lead
from apps.organizations.models import OrganizationMember


class LeadSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    contact_id = serializers.UUIDField(source="contact.id", read_only=True, allow_null=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=OrganizationMember.objects.all(),
        allow_null=True,
        required=False,
    )
    assigned_to_name = serializers.SerializerMethodField()
    converted_to_contact_id = serializers.UUIDField(source="converted_to_contact.id", read_only=True, allow_null=True)
    created_by_name = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            "id",
            "organization_id",
            "contact_id",
            "name",
            "email",
            "phone",
            "company",
            "job_title",
            "website",
            "source",
            "status",
            "score",
            "priority",
            "estimated_value",
            "currency",
            "assigned_to",
            "assigned_to_name",
            "notes",
            "tags",
            "custom_fields",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "converted_at",
            "converted_to_contact_id",
            "last_activity_at",
        ]
        read_only_fields = [
            "id",
            "organization_id",
            "contact_id",
            "assigned_to_name",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "converted_at",
            "converted_to_contact_id",
        ]
    
    def get_assigned_to_name(self, obj):
        """Get assigned member's name"""
        if obj.assigned_to and obj.assigned_to.user:
            return f"{obj.assigned_to.user.first_name} {obj.assigned_to.user.last_name}".strip()
        return None
    
    def get_created_by_name(self, obj):
        """Get creator's name"""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None
    
    def get_tags(self, obj):
        """Get tag names"""
        return [tag.name for tag in obj.tags.all()]
    
    def validate_score(self, value):
        """Validate score is between 0-100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value
    
    def validate(self, attrs):
        """Validate lead data"""
        organization = self.context.get("organization")
        
        # Validate assigned_to belongs to organization
        assigned_to = attrs.get("assigned_to")
        if assigned_to and organization:
            if assigned_to.organization_id != organization.id:
                raise serializers.ValidationError({"assigned_to": "Assigned member must belong to the organization."})
        
        return attrs
    
    def create(self, validated_data):
        """Create lead with tags"""
        tags_data = self.initial_data.get("tags", [])
        organization = self.context["organization"]
        
        # Set default score if not provided
        if "score" not in validated_data:
            validated_data["score"] = 0
        
        lead = super().create(validated_data)
        
        # Add tags
        if tags_data:
            if isinstance(tags_data[0], str):
                # Tag names provided
                tags = Tag.objects.filter(name__in=tags_data, organization=organization)
            else:
                # Tag IDs provided
                tags = Tag.objects.filter(id__in=tags_data, organization=organization)
            lead.tags.set(tags)
        
        return lead
    
    def update(self, instance, validated_data):
        """Update lead with tags"""
        tags_data = self.initial_data.get("tags")
        lead = super().update(instance, validated_data)
        
        # Update tags if provided
        if tags_data is not None:
            if isinstance(tags_data, list) and tags_data:
                if isinstance(tags_data[0], str):
                    tags = Tag.objects.filter(name__in=tags_data, organization=lead.organization)
                else:
                    tags = Tag.objects.filter(id__in=tags_data, organization=lead.organization)
                lead.tags.set(tags)
            else:
                lead.tags.clear()
        
        return lead


class LeadStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating lead status"""
    status = serializers.ChoiceField(choices=Lead.Status.choices)
    
    def validate_status(self, value):
        """Validate status transition"""
        return value


class LeadScoreUpdateSerializer(serializers.Serializer):
    """Serializer for updating lead score"""
    score = serializers.IntegerField(min_value=0, max_value=100)


class LeadConvertSerializer(serializers.Serializer):
    """Serializer for converting lead to contact"""
    create_contact = serializers.BooleanField(default=True)
    contact_data = serializers.DictField(required=False)
    
    def validate(self, attrs):
        """Validate conversion data"""
        if attrs.get("create_contact") and not attrs.get("contact_data"):
            raise serializers.ValidationError("contact_data is required when create_contact is True.")
        return attrs

