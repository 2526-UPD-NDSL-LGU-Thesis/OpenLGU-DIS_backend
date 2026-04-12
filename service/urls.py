"""
API Endpoints for Services.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('api/service/<int:service_id>', views.claim_service)
]
