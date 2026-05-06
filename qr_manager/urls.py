"""
API Endpoints for QR Manager.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('qr/', views.decrypt_qr),
    path('qr/image/', views.decrypt_qr_image)
]
