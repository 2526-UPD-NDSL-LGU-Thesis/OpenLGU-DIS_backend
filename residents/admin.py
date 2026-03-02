from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from service.models import ServiceClaim


class ResidentClaimInline(admin.TabularInline):
    model = ServiceClaim
    extra = 0
    readonly_fields = ("service", "claimed_at")
    can_delete = False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "pcn", "issued_at", "proof_of_residence", "verified",
    )

    list_filter = (
        "verified",
    )

    search_fields = (
        "pcn",
        "email",
    )

    inlines = [ResidentClaimInline]
