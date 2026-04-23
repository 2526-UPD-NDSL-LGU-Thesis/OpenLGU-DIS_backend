"""
API Endpoints for QR Manager.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('qr/verify/', views.decrypt_qr)
]
