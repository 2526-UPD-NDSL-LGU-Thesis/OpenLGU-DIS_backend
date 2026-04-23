"""
API Endpoints for Services.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('service/<str:service_id>/', views.claim_service),
    path('service/<str:service_id>/pcn/', views.claim_service_with_pcn)
]
#TODO: Define a better URL scheme
