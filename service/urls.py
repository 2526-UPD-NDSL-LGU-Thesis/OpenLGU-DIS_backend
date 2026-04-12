"""
API Endpoints for Services.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('api/service/<int:service_id>/', views.claim_service),
    path('api/service/<int:service_id>/pcn/', views.claim_service_with_pcn)
]
#TODO: Define a better URL scheme
