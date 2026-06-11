from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from rest_framework.permissions import BasePermission


class HasServiceClaimRole(BasePermission):
    def __init__(self) -> None:
        if not (
            Group.objects.filter(name="Service Claim Admin").exists() and
            Group.objects.filter(name="Service Claim Employee").exists()
        ):
            raise ImproperlyConfigured(
                "Missing required groups."
                "Run `python manage.py createbasegroups`."
            )
        super().__init__()
    def has_permission(self, request, view):
        if not request.user:
            return False
        
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(name__in=[
            "Service Claim Admin", "Service Claim Employee"
        ]).exists():
            return True