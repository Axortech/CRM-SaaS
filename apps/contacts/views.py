import csv
from datetime import datetime, timedelta

from django.db.models import Count, Q
from django.http import HttpResponse
from django_filters.rest_framework import FilterSet, filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
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
    TagSerializer,
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

    @extend_schema(
        summary="Bulk delete contacts",
        description="Delete multiple contacts at once.",
        request=ContactBulkOperationSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}, "deleted_count": {"type": "integer"}}}},
    )
    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request, *args, **kwargs):
        serializer = ContactBulkOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = self._get_request_organization()
        contact_ids = serializer.validated_data["contact_ids"]
        queryset = self.get_queryset().filter(id__in=contact_ids)
        deleted_count, _ = queryset.delete()
        return Response({
            "message": f"{deleted_count} contacts deleted",
            "deleted_count": deleted_count
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Bulk update contacts",
        description="Update multiple contacts at once.",
        request=ContactBulkOperationSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}, "updated_count": {"type": "integer"}}}},
    )
    @action(detail=False, methods=["post"], url_path="bulk-update")
    def bulk_update(self, request, *args, **kwargs):
        serializer = ContactBulkOperationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_ids = serializer.validated_data["contact_ids"]
        updates = serializer.validated_data.get("updates", {})
        
        organization = self._get_request_organization()
        queryset = self.get_queryset().filter(id__in=contact_ids, organization=organization)
        
        # Handle tags separately if present
        tags = updates.pop("tags", None) if "tags" in updates else None
        
        updated_count = 0
        if updates:
            updated_count = queryset.update(**updates)
        
        if tags:
            # Update tags for all contacts
            for contact in queryset:
                if isinstance(tags, list):
                    tag_objects = Tag.objects.filter(id__in=tags, organization=organization)
                    contact.tags.set(tag_objects)
            updated_count = queryset.count()
        
        return Response({
            "message": f"{updated_count} contacts updated",
            "updated_count": updated_count
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get contact activities",
        description="Get a paginated list of activities for a contact.",
        responses={200: {"type": "object"}},
    )
    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        """Get contact activities"""
        from apps.activities.serializers import ActivitySerializer
        from rest_framework.pagination import PageNumberPagination
        
        contact = self.get_object()
        activities = Activity.objects.filter(contact=contact).select_related("created_by").order_by("-occurred_at")
        
        # Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = request.query_params.get("page_size", 10)
        page = paginator.paginate_queryset(activities, request)
        
        if page is not None:
            serializer = ActivitySerializer(page, many=True, context=self.get_serializer_context())
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ActivitySerializer(activities, many=True, context=self.get_serializer_context())
        return Response({"data": serializer.data})

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

    @extend_schema(
        summary="Get contact statistics",
        description="Get statistics about contacts in the organization.",
        responses={200: {"type": "object"}},
    )
    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request, *args, **kwargs):
        """Get contact statistics"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(organization=organization)
        
        # Total counts
        total = queryset.count()
        active = queryset.filter(stage=Contact.Stage.CUSTOMER).count()
        inactive = queryset.filter(stage=Contact.Stage.INACTIVE).count()
        
        # By source
        by_source = {}
        for source_value, source_label in Contact.Source.choices:
            count = queryset.filter(source=source_value).count()
            if count > 0:
                by_source[source_value] = count
        
        # By tag
        by_tag = {}
        tags = Tag.objects.filter(organization=organization).annotate(
            contact_count=Count("contacts")
        ).filter(contact_count__gt=0)
        for tag in tags:
            by_tag[tag.name] = tag.contact_count
        
        # Recent count (last 30 days)
        recent_date = datetime.now() - timedelta(days=30)
        recent_count = queryset.filter(created_at__gte=recent_date).count()
        
        return Response({
            "total": total,
            "active": active,
            "inactive": inactive,
            "by_source": by_source,
            "by_tag": by_tag,
            "recent_count": recent_count,
        })

    @extend_schema(
        summary="List contact tags",
        description="Get a list of all tags used for contacts in the organization.",
        responses={200: TagSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="tags")
    def list_tags(self, request, *args, **kwargs):
        """List all contact tags"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tags = Tag.objects.filter(organization=organization).annotate(
            contact_count=Count("contacts")
        ).order_by("name")
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create contact tag",
        description="Create a new tag for contacts.",
        request=TagSerializer,
        responses={201: TagSerializer},
    )
    @action(detail=False, methods=["post"], url_path="tags")
    def create_tag(self, request, *args, **kwargs):
        """Create a new contact tag"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = TagSerializer(
            data=request.data,
            context={"organization": organization}
        )
        serializer.is_valid(raise_exception=True)
        tag = serializer.save(organization=organization)
        return Response(TagSerializer(tag).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Import contacts from CSV",
        description="Import contacts from a CSV file. Returns import results with errors if any.",
        request={"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}},
        responses={200: {"type": "object"}},
    )
    @action(detail=False, methods=["post"], url_path="import")
    def import_contacts(self, request, *args, **kwargs):
        """Import contacts from CSV file"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if "file" not in request.FILES:
            return Response(
                {"error": "CSV file is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        csv_file = request.FILES["file"]
        if not csv_file.name.endswith(".csv"):
            return Response(
                {"error": "File must be a CSV file."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Read CSV
        decoded_file = csv_file.read().decode("utf-8")
        csv_reader = csv.DictReader(decoded_file.splitlines())
        
        total = 0
        successful = 0
        failed = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            total += 1
            try:
                # Map CSV columns to contact fields
                contact_data = {
                    "first_name": row.get("first_name", ""),
                    "last_name": row.get("last_name", ""),
                    "email": row.get("email", ""),
                    "phone": row.get("phone", ""),
                    "mobile": row.get("mobile", ""),
                    "job_title": row.get("job_title", ""),
                    "source": row.get("source", ""),
                }
                
                # Validate and create contact
                serializer = ContactSerializer(
                    data=contact_data,
                    context={"organization": organization}
                )
                if serializer.is_valid():
                    serializer.save(organization=organization, created_by=request.user)
                    successful += 1
                else:
                    failed += 1
                    errors.append({
                        "row": row_num,
                        "field": list(serializer.errors.keys())[0] if serializer.errors else "unknown",
                        "message": str(serializer.errors),
                        "data": contact_data
                    })
            except Exception as e:
                failed += 1
                errors.append({
                    "row": row_num,
                    "field": "unknown",
                    "message": str(e),
                    "data": row
                })
        
        return Response({
            "total": total,
            "successful": successful,
            "failed": failed,
            "errors": errors
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Export contacts to CSV",
        description="Export contacts to a CSV file. Uses the same filters as the list endpoint.",
        responses={200: {"type": "string", "format": "binary"}},
    )
    @action(detail=False, methods=["get"], url_path="export")
    def export_contacts(self, request, *args, **kwargs):
        """Export contacts to CSV file"""
        organization = self._get_request_organization()
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get filtered queryset (same as list)
        queryset = self.get_queryset().filter(organization=organization)
        
        # Apply filters from query params
        queryset = self.filter_queryset(queryset)
        
        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="contacts_{organization.slug}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        # Write header
        writer.writerow([
            "first_name", "last_name", "email", "phone", "mobile",
            "company", "job_title", "source", "stage", "tags"
        ])
        
        # Write data
        for contact in queryset:
            tags = ",".join([tag.name for tag in contact.tags.all()])
            writer.writerow([
                contact.first_name,
                contact.last_name,
                contact.email or "",
                contact.phone or "",
                contact.mobile or "",
                contact.company.name if contact.company else "",
                contact.job_title or "",
                contact.source or "",
                contact.stage or "",
                tags
            ])
        
        return response

    @extend_schema(
        summary="Upload contact avatar",
        description="Upload an avatar image for a contact.",
        request={"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}},
        responses={200: {"type": "object", "properties": {"avatar_url": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post"], url_path="avatar")
    def upload_avatar(self, request, pk=None):
        """Upload contact avatar"""
        contact = self.get_object()
        organization = self._get_request_organization()
        
        if not organization:
            return Response(
                {"error": "Organization parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if "file" not in request.FILES:
            return Response(
                {"error": "File is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES["file"]
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if uploaded_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Only image files are allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return Response(
                {"error": "File size exceeds 5MB limit."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save file (in production, this would upload to S3/CDN)
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Generate filename
        file_ext = os.path.splitext(uploaded_file.name)[1] or ".png"
        filename = f"avatars/contact_{contact.id}{file_ext}"
        
        # Save file
        file_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
        
        # Get file URL
        # In production, this would be a CDN URL
        avatar_url = default_storage.url(file_path)
        
        # Store avatar URL in custom_fields or add avatar_url field to model
        # For now, storing in custom_fields
        if not contact.custom_fields:
            contact.custom_fields = {}
        contact.custom_fields["avatar_url"] = avatar_url
        contact.save(update_fields=["custom_fields"])
        
        return Response({"avatar_url": avatar_url}, status=status.HTTP_200_OK)
