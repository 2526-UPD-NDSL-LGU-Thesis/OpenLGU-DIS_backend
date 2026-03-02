from django.contrib import admin
from .models import Service, ServiceClaim


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
    list_display = (
        "user",
        "service",
        "claimed_at",
    )

    list_filter = (
        "service",
        "claimed_at",
    )

    search_fields = (
        "user__pcn",
    )

    autocomplete_fields = ("user", "service")