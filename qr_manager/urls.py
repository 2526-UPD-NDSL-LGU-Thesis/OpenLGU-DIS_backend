"""
API Endpoints for QR Manager.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('api/qr/verify/', views.decrypt_qr)
]
