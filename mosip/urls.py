"""
API Endpoints for MOSIP functions.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('api/auth/otp/start/', views.auth_start_otp),
    path('api/auth/otp/verify/', views.auth_via_otp),
    path('api/auth/demo/', views.auth_via_demographics),
    path('api/kyc/otp/start/', views.kyc_start_otp),
    path('api/kyc/otp/verify/', views.kyc_via_otp),
    path('api/kyc/demo/', views.kyc_via_demographics),
    path('api/mosip/ping/', views.ping)
]
