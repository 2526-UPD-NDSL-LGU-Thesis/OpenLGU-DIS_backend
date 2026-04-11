from django.contrib import admin
from .models import Service, ServiceClaim
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group, User


# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


admin.site.unregister(Group)


class UserInline(admin.TabularInline):
    model = User.groups.through
    extra = 1


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    inlines = [UserInline]


class ServiceClaimInline(admin.TabularInline):
    model = ServiceClaim
    extra = 0
    readonly_fields = ("user", "claimed_at")
    can_delete = False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "max_claims",
        "period_seconds",
        "active",
    )

    list_filter = ("active",)
    search_fields = ("name",)

    inlines = [ServiceClaimInline]


@admin.register(ServiceClaim)
class ServiceClaimAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "user", "service", "claimed_at",)

    list_filter = ("service", "claimed_at",)

    search_fields = ("user__pcn",)

    autocomplete_fields = ("user", "service")
