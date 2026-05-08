"""
API Endpoints for QR Manager.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('verify/qr/', views.decrypt_qr),
    path('verify/qr/image/', views.decrypt_qr_image)
]
