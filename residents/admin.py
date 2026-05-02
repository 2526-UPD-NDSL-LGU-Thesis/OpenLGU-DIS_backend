from django.contrib import admin
from .models import Resident, ResidentSector
from service.models import ServiceClaim


@admin.register(ResidentSector)
class SectorAdmin(admin.ModelAdmin):
    list_display = (
        "name", "description",
    )

    search_fields = (
        "name", "short_name",
    )


class ResidentClaimInline(admin.TabularInline):
    model = ServiceClaim
    extra = 0
    readonly_fields = ("service", "claimed_at")
    can_delete = False


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = (
        "uin", "pcn", "issued_at",
        "proof_of_residence", "active", "email", "phone_number", "profile_image",
    )

    list_filter = (
        "active",
    )

    search_fields = (
        "pcn",
        "uin",
    )

    inlines = [ResidentClaimInline]
