'''
Generate base permission groups.
'''

from typing import Any

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from residents.models import Resident, Sector
from service.models import Service, Claim


GROUP_PERMISSIONS = {
    "Sector Admin": [
        "residents.add_sector",
        "residents.change_sector",
        "residents.delete_sector",
        "residents.view_sector",
        "residents.change_resident",
        "residents.view_resident",
        "service.view_service",
    ],

    "Sector Employee": [
        "residents.view_sector",
        "residents.change_resident",
        "residents.view_resident",
        "service.view_service",
    ],

    "Service Admin": [
        "service.add_service",
        "service.change_service",
        "service.delete_service",
        "service.view_service",
        "service.add_claim",
        "service.change_claim",
        "service.delete_claim",
        "service.view_claim",
        "residents.view_resident",
    ],

    "Service Employee": [
        "service.view_service",
        "service.view_claim",
        "residents.view_resident",
    ],

    "Service Claim Admin": [
        "service.view_service",
        "service.add_claim",
        "service.change_claim",
        "service.delete_claim",
        "service.view_claim",
        "residents.view_resident",
    ],

    "Service Claim Employee": [
        "service.view_service",
        "service.add_claim",
        "service.view_claim",
        "residents.view_resident",
    ],

    "ID Management Admin": [
        "residents.add_resident",
        "residents.change_resident",
        "residents.delete_resident",
        "residents.view_resident",
    ],

    "ID Management Employee": [
        "residents.add_resident",
        "residents.change_resident",
        "residents.view_resident",
    ],
}


class Command(BaseCommand):
    help = "Generate base permission groups."

    def handle(self, *args: Any, **options: Any) -> None :
        for group_name, permission_names in GROUP_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)

            permissions = []

            for permission_name in permission_names:
                app_label, codename = permission_name.split('.')

                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )

                permissions.append(permission)
        
            group.permissions.set(permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {group_name} group with {len(permissions)} permissions."
                )
            )
