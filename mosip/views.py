from django.http import HttpRequest, JsonResponse
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status

from .models import (
    MOSIPBaseResponse, MOSIPKYCResponse, MOSIPAuthResponse, MOSIPGenOTPResponse
)

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

@api_view(['POST'])
def auth_via_demographics(request : HttpRequest) -> JsonResponse :
    data = request.data
    uid = data.pop("uid")

    mosip_response = MOSIPAuthResponse.from_demographics(
        uid=uid,
        **data
    )

    return JsonResponse(
        mosip_response.model_dump(),
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def auth_start_otp(request : HttpRequest) -> JsonResponse :
    data = request.data
    uid = data.pop("uid")

    mosip_response = MOSIPGenOTPResponse.start_otp(
        uid=uid,
        **data
    )

    return JsonResponse(
        { "txn_id" : mosip_response.transaction_id },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def auth_via_otp(request : HttpRequest) -> JsonResponse :
    data = request.data
    uid = data.pop("uid")
    txn_id = data.pop("txn_id")
    otp = data.pop("otp")

    mosip_response = MOSIPAuthResponse.from_otp(
        uid=uid,
        txn_id=txn_id,
        otp=otp
    )

    return JsonResponse(
        mosip_response.model_dump(),
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def kyc_via_demographics(request : HttpRequest) -> JsonResponse :
    data = request.data
    uid = data.pop("uid")

    mosip_response = MOSIPKYCResponse.from_demographics(
        uid=uid,
        **data
    )

    return JsonResponse(
        mosip_response.model_dump(),
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def kyc_start_otp(request : HttpRequest) -> JsonResponse :
    data = request.data
    uid = data.pop("uid")

    mosip_response = MOSIPGenOTPResponse.start_otp(
        uid=uid,
        **data
    )

    return JsonResponse(
        { "txn_id" : mosip_response.transaction_id },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def kyc_via_otp(request : HttpRequest) -> JsonResponse :
    data = request.data
    uid = data.pop("uid")
    txn_id = data.pop("txn_id")
    otp = data.pop("otp")

    mosip_response = MOSIPKYCResponse.from_otp(
        uid=uid,
        txn_id=txn_id,
        otp=otp
    )

    return JsonResponse(
        mosip_response.model_dump(),
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
def ping(_) -> JsonResponse :
    return JsonResponse({ "message": "pong" }, status=200)

#TODO: change 200 statuses to 202 if async operations
#TODO: write errors
