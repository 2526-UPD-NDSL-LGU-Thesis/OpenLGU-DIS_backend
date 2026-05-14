from django.contrib import admin
from .models import Resident, ResidentSector
from service.models import Claim


@admin.register(ResidentSector)
class SectorAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "description",
    )

    search_fields = (
        "id", "name",
    )


class ResidentClaimInline(admin.TabularInline):
    model = Claim
    extra = 0
    readonly_fields = ("service", "claimed_at")
    can_delete = False


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = (
        "uin", "pcn", "issued_at",
        "proof_of_residence", "profile_image",
        "active",
    )

    list_filter = (
        "active",
    )

    search_fields = (
        "pcn",
        "uin",
    )

    inlines = [ResidentClaimInline]
