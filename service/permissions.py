from rest_framework.permissions import BasePermission


class CanAccessServiceClaim(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser:
            return True
        
        return obj.service.allowed_groups.filter(
            id__in=user.groups.values_list('id', flat=True)
        ).exists()
