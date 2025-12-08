from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import OrganizationScopedModel, UserTrackedModel
from apps.contacts.models import Tag


class Lead(OrganizationScopedModel, UserTrackedModel):
    """Lead model for managing potential customers"""
    
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        UNQUALIFIED = "unqualified", "Unqualified"
        CONVERTED = "converted", "Converted"
    
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"
    
    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        REFERRAL = "referral", "Referral"
        SOCIAL = "social", "Social Media"
        CAMPAIGN = "campaign", "Campaign"
        OTHER = "other", "Other"
    
    # Basic information
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    website = models.URLField(blank=True)
    
    # Lead tracking
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NEW)
    source = models.CharField(max_length=32, choices=Source.choices, blank=True)
    score = models.IntegerField(default=0, help_text="Lead score from 0-100")
    priority = models.CharField(max_length=32, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Value tracking
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="USD")
    
    # Assignment
    assigned_to = models.ForeignKey(
        "organizations.OrganizationMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_leads",
    )
    
    # Additional data
    notes = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="leads")
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Conversion tracking
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_to_contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="converted_from_leads",
    )
    last_activity_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("organization", "status")),
            models.Index(fields=("organization", "assigned_to")),
            models.Index(fields=("organization", "score")),
            models.Index(fields=("organization", "created_at")),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.company})" if self.company else self.name
    
    def mark_converted(self, contact=None):
        """Mark lead as converted"""
        self.status = self.Status.CONVERTED
        self.converted_at = timezone.now()
        if contact:
            self.converted_to_contact = contact
        self.save(update_fields=["status", "converted_at", "converted_to_contact"])

