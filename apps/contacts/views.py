from django.db.models import Count
from django_filters.rest_framework import FilterSet, filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import OrganizationScopedViewSet
from apps.activities.models import Activity
from apps.contacts.models import Contact, Tag
from apps.contacts.serializers import (
    ContactBulkImportSerializer,
    ContactBulkOperationSerializer,
    ContactMergeSerializer,
    ContactSerializer,
)
from apps.opportunities.models import Opportunity
from apps.tasks.models import Task


class ContactFilterSet(FilterSet):
    stage = filters.CharFilter(field_name="stage")
    source = filters.CharFilter(field_name="source")
    owner = filters.UUIDFilter(field_name="owner_id")
    company = filters.UUIDFilter(field_name="company_id")
    tags = filters.UUIDFilter(field_name="tags__id")

    class Meta:
        model = Contact
        fields = ["stage", "source", "owner", "company", "tags"]


class ContactViewSet(OrganizationScopedViewSet):
    schema_tags = ["Contacts"]
    queryset = Contact.objects.select_related("company", "owner").prefetch_related("tags")
    serializer_class = ContactSerializer
    filterset_class = ContactFilterSet
    search_fields = ["first_name", "last_name", "email", "phone", "company__name"]
    ordering_fields = ["first_name", "last_name", "created_at", "updated_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self._get_request_organization()
        if organization:
            return queryset.filter(organization=organization)
        return queryset

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request, *args, **kwargs):
        serializer = ContactBulkImportSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"detail": "organization parameter is required for bulk import."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        created = []
        for payload in serializer.validated_data["contacts"]:
            contact_serializer = ContactSerializer(
                data=payload,
                context={"organization": organization},
            )
            contact_serializer.is_valid(raise_exception=True)
            contact = contact_serializer.save(organization=organization, created_by=request.user)
            created.append(contact)
        return Response(
            {"imported": len(created), "ids": [str(contact.id) for contact in created]},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request, *args, **kwargs):
        serializer = ContactBulkOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = self._get_request_organization()
        queryset = self.get_queryset().filter(id__in=serializer.validated_data["ids"])
        deleted, _ = queryset.delete()
        return Response({"deleted": deleted}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="bulk-update")
    def bulk_update(self, request, *args, **kwargs):
        serializer = ContactBulkOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.get("data", {})
        updated = self.get_queryset().filter(id__in=serializer.validated_data["ids"]).update(**data)
        return Response({"updated": updated}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        contact = self.get_object()
        activities = Activity.objects.filter(contact=contact).order_by("-occurred_at")
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

    @action(detail=True, methods=["get"], url_path="opportunities")
    def contact_opportunities(self, request, pk=None):
        contact = self.get_object()
        opportunities = Opportunity.objects.filter(contact=contact)
        return Response(
            [
                {
                    "id": str(opportunity.id),
                    "name": opportunity.name,
                    "stage": opportunity.stage.name if opportunity.stage else None,
                    "amount": opportunity.amount,
                    "status": opportunity.status,
                }
                for opportunity in opportunities
            ]
        )

    @action(detail=True, methods=["get"], url_path="tasks")
    def contact_tasks(self, request, pk=None):
        contact = self.get_object()
        tasks = Task.objects.filter(contact=contact)
        return Response(
            [
                {
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "due_date": task.due_date,
                }
                for task in tasks
            ]
        )

    @action(detail=True, methods=["post"], url_path="tags")
    def add_tags(self, request, pk=None):
        contact = self.get_object()
        tag_ids = request.data.get("tag_ids", [])
        tags = Tag.objects.filter(id__in=tag_ids, organization=contact.organization)
        contact.tags.add(*tags)
        return Response({"tags": list(contact.tags.values_list("id", flat=True))})

    @action(detail=True, methods=["delete"], url_path="tags/(?P<tag_id>[^/.]+)")
    def remove_tag(self, request, pk=None, tag_id=None):
        contact = self.get_object()
        try:
            tag = contact.tags.get(id=tag_id)
        except Tag.DoesNotExist:
            return Response({"detail": "Tag not found."}, status=status.HTTP_404_NOT_FOUND)
        contact.tags.remove(tag)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], url_path="merge")
    def merge(self, request, *args, **kwargs):
        serializer = ContactMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        primary = self.get_queryset().get(id=serializer.validated_data["primary_id"])
        secondary = self.get_queryset().get(id=serializer.validated_data["secondary_id"])
        # Transfer tags and tasks/opportunities references if needed
        primary.tags.add(*secondary.tags.all())
        Task.objects.filter(contact=secondary).update(contact=primary)
        Activity.objects.filter(contact=secondary).update(contact=primary)
        Opportunity.objects.filter(contact=secondary).update(contact=primary)
        secondary.delete()
        return Response({"detail": "Contacts merged.", "primary_id": str(primary.id)})

    @action(detail=False, methods=["get"], url_path="duplicates")
    def duplicates(self, request, *args, **kwargs):
        duplicates = (
            self.get_queryset()
            .values("email")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )
        duplicate_emails = [item["email"] for item in duplicates if item["email"]]
        contacts = self.get_queryset().filter(email__in=duplicate_emails).order_by("email")
        grouped = {}
        for contact in contacts:
            grouped.setdefault(contact.email, []).append(
                {
                    "id": str(contact.id),
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                }
            )
        return Response(
            [{"email": email, "contacts": grouped.get(email, [])} for email in duplicate_emails]
        )
