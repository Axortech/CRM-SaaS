from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from apps.organizations.models import Organization, OrganizationMember, Role

DEFAULT_ROLE_DEFINITIONS: List[Dict] = [
    {"name": "Admin", "is_system_role": True, "permissions": ["*"]},
    {"name": "Staff", "is_system_role": True, "permissions": []},
]


def _generate_unique_slug(base_value: str) -> str:
    base_slug = slugify(base_value)
    slug = base_slug
    index = 1
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{index}"
        index += 1
    return slug


@transaction.atomic
def create_organization_with_owner(
    *,
    owner,
    name: str,
    timezone: str = "UTC",
    admin_user: Optional = None,
) -> Organization:
    slug = _generate_unique_slug(name)
    organization = Organization.objects.create(
        name=name,
        slug=slug,
        owner=owner,
        timezone=timezone,
    )
    ensure_default_roles(organization)
    if admin_user:
        admin_role = Role.objects.get(organization=organization, name="Admin")
        OrganizationMember.objects.create(
            organization=organization,
            user=admin_user,
            role=admin_role,
            is_active=True,
            invitation_accepted=True,
        )
    return organization


def ensure_default_roles(organization: Organization) -> Iterable[Role]:
    roles = []
    for definition in DEFAULT_ROLE_DEFINITIONS:
        role, _ = Role.objects.get_or_create(
            organization=organization,
            name=definition["name"],
            defaults={
                "is_system_role": definition.get("is_system_role", False),
                "permissions": definition.get("permissions", []),
            },
        )
        roles.append(role)
    return roles


def user_is_org_admin(user, organization: Organization) -> bool:
    if organization.owner_id == user.id:
        return True
    return OrganizationMember.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
        role__name__in=["Admin"],
    ).exists()


def user_in_organization(user, organization: Organization) -> bool:
    if organization.owner_id == user.id:
        return True
    return OrganizationMember.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
    ).exists()


def organizations_for_user(user):
    if not user.is_authenticated:
        return Organization.objects.none()
    return Organization.objects.filter(
        Q(owner=user) | Q(members__user=user, members__is_active=True)
    ).distinct()


def organization_ids_for_user(user) -> List:
    return list(organizations_for_user(user).values_list("id", flat=True))
