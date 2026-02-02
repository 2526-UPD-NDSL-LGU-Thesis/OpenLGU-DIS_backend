from django.contrib import admin

from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "pcn", "issued_at", "proof_of_residence", "verified",
    )
