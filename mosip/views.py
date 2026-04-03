from django.http import HttpRequest
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from .models import (
    MOSIPBaseResponse, MOSIPKYCResponse, MOSIPAuthResponse, MOSIPGenOTPResponse
)

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

@api_view(['POST'])
def auth_via_demographics(request : HttpRequest) :
    mosip_response = MOSIPAuthResponse.from_demographics(
        
    )


@api_view(['POST'])
def auth_start_otp(request : HttpRequest) :
    mosip_response = MOSIPGenOTPResponse.start_otp(

    )


@api_view(['POST'])
def auth_via_otp(request : HttpRequest) :
    mosip_response = MOSIPAuthResponse.from_otp(
        
    )


@api_view(['POST'])
def kyc_via_demographics(request : HttpRequest) :
    mosip_response = MOSIPKYCResponse.from_demographics(
        
    )


@api_view(['POST'])
def kyc_start_otp(request : HttpRequest) :
    mosip_response = MOSIPGenOTPResponse.start_otp(
        
    )


@api_view(['POST'])
def kyc_via_otp(request : HttpRequest) :
    mosip_response = MOSIPKYCResponse.from_otp(
        
    )