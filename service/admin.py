from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.models import Group as BaseGroup
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest
from .models import (
    Service, Claim, Group, Assignment
)


# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


admin.site.unregister(BaseGroup)
admin.site.unregister(User)


class UserInline(admin.TabularInline):
    model = User.groups.through
    extra = 1


@admin.register(BaseGroup)
class GroupAdmin(BaseGroupAdmin):
    inlines = [UserInline]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    class Meta:
        proxy = True

    def __str__(self) -> str:
        return self.username if self.username else self.get_short_name()


class ClaimInline(admin.TabularInline):
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

    inlines = [ClaimInline]


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "user", "service", "amount", "claimed_at", "claimed_by")

    list_filter = ("service", "claimed_by",)

    search_fields = ("transaction_id", "user__uin", "user__pcn",)

    autocomplete_fields = ("user", "service")


@admin.register(Group)
class ClaimingGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
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

    def save_model(self, request: HttpRequest, obj: Any, form: ModelForm, change: bool) -> None:
        if not obj.assigned_by:
            obj.assiged_by = request.user
        
        return super().save_model(request, obj, form, change)
