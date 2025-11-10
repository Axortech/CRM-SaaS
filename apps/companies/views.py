from django_filters.rest_framework import FilterSet, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.activities.models import Activity
from apps.companies.models import Company
from apps.companies.serializers import CompanySerializer
from apps.contacts.models import Contact
from apps.opportunities.models import Opportunity


class CompanyFilterSet(FilterSet):
    owner = filters.UUIDFilter(field_name="owner_id")
    industry = filters.CharFilter(field_name="industry")

    class Meta:
        model = Company
        fields = ["owner", "industry", "parent_company"]


class CompanyViewSet(OrganizationScopedViewSet):
    schema_tags = ["Companies"]
    queryset = Company.objects.select_related("owner", "parent_company")
    serializer_class = CompanySerializer
    filterset_class = CompanyFilterSet
    search_fields = ["name", "website", "city", "state", "country"]
    ordering_fields = ["name", "created_at", "updated_at"]

    @action(detail=True, methods=["get"], url_path="contacts")
    def contacts(self, request, pk=None):
        company = self.get_object()
        contacts = Contact.objects.filter(company=company)
        return Response(
            [
                {
                    "id": str(contact.id),
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "email": contact.email,
                }
                for contact in contacts
            ]
        )

    @action(detail=True, methods=["get"], url_path="opportunities")
    def opportunities(self, request, pk=None):
        company = self.get_object()
        opportunities = Opportunity.objects.filter(company=company)
        return Response(
            [
                {
                    "id": str(opportunity.id),
                    "name": opportunity.name,
                    "stage": opportunity.stage.name if opportunity.stage else None,
                    "amount": opportunity.amount,
                }
                for opportunity in opportunities
            ]
        )

    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        company = self.get_object()
        activities = Activity.objects.filter(company=company).order_by("-occurred_at")
        return Response(
            [
                {
                    "id": str(activity.id),
                    "type": activity.activity_type,
                    "subject": activity.subject,
                    "occurred_at": activity.occurred_at,
                }
                for activity in activities
            ]
        )
