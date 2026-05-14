from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.db.models.query import QuerySet
from django.http import HttpRequest
from .models import (
    Service, Claim, ClaimGroup, ServiceAssignment
)


# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


admin.site.unregister(Group)
admin.site.unregister(User)


class UserInline(admin.TabularInline):
    model = User.groups.through
    extra = 1


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    inlines = [UserInline]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    class Meta:
        proxy = True

    def __str__(self) -> str:
        return self.username if self.username else self.get_short_name()


class ServiceClaimInline(admin.TabularInline):
    model = Claim
    extra = 0
    readonly_fields = ("user", "claimed_at")
    can_delete = False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "claim_type", "stocks_type", "refresh_interval",
                    "max_claims_per_user", "stocks", "active",)

    list_filter = ("claim_type", "stocks_type", "refresh_interval", "active",)
    search_fields = ("name",)

    inlines = [ServiceClaimInline]


@admin.register(Claim)
class ServiceClaimAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "user", "service", "amount", "claimed_at", "claimed_by")

    list_filter = ("service", "claimed_by",)

    search_fields = ("transaction_id", "user__uin", "user__pcn",)

    autocomplete_fields = ("user", "service")


@admin.register(ClaimGroup)
class ClaimGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(ServiceAssignment)
class ServiceAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "assigned_by",
        "last_update",
    )

    list_filter = (
        "last_update",
        "groups",
    )

    search_fields = (
        "user__username",
        "user__email",
        "assigned_by__username",
    )

    filter_horizontal = ("groups",)

    readonly_fields = ("last_update",)
