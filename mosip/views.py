from django.http import HttpRequest
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from .models import (
    MOSIPBaseResponse, MOSIPKYCResponse, MOSIPAuthResponse
)


@api_view(['POST'])
def start_otp(request : HttpRequest) :
    pass


@api_view(['POST'])
def auth_via_demographics(request : HttpRequest) :
    pass


@api_view(['POST'])
def auth_via_otp(request : HttpRequest) :
    pass


@api_view(['POST'])
def kyc_via_demographics(request : HttpRequest) :
    pass


@api_view(['POST'])
def kyc_via_otp(request : HttpRequest) :
    pass