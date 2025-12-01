from django.contrib import admin

from .models import CompSciLabID, CompSciDeptID, CompSciLabs

# Register your models here.

@admin.register(CompSciLabID)
class CompSciLabIDAdmin(admin.ModelAdmin):
    list_display = (
        "id", "cslab", "csdept", "issued_at", "file", "verified"
    )

    list_filter = (
        "id", "cslab", "csdept", "verified"
    )

    search_fields = (
        "id",
        "cslab__abbr",
        "cslab__name",
        "csdept__id",
    )

@admin.register(CompSciDeptID)
class CompSciDeptIDAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "gender", "dob", "location1", "phone", "email"
    )


@admin.register(CompSciLabs)
class CompSciLabsAdmin(admin.ModelAdmin):
    list_display = (
        "abbr", "name"
    )