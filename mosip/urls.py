"""
API Endpoints for MOSIP functions.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('auth/otp/start/', views.auth_start_otp),
    path('auth/otp/verify/', views.auth_via_otp),
    path('auth/demo/', views.auth_via_demographics),
    path('kyc/otp/start/', views.kyc_start_otp),
    path('kyc/otp/verify/', views.kyc_via_otp),
    path('kyc/demo/', views.kyc_via_demographics),
    path('mosip/ping/', views.ping)
]
