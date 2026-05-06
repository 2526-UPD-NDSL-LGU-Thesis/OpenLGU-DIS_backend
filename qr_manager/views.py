"""
API views for QR Manager app.
"""


from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status

from residents.models import Resident
from .utils import read_qr, read_qr_image
from .classes import QRTypes, DRFErrors


@api_view(['POST'])
def decrypt_qr(request : HttpRequest) -> Response :
    data = request.data

    try:
        b45_qr = data.pop("qr")
    except KeyError:
        return Response(
            {
                "error" : DRFErrors.InvalidPOSTBody,
                "details" : "Expected qr, got None instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        type, payload = read_qr(b45_qr).values()
    except Exception as err:
        return Response(
            {
                "error"   : DRFErrors.QRVerificationFailed,
                "details" : str(err)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if type == QRTypes.OpenLGUQR:
        if not Resident.objects.filter(uin=payload[169][75]).exists():
            return Response(
                {
                    "error"   : DRFErrors.DjangoUserDoesNotExist,
                    "details" : f"User {payload[169][75]} does not exist." 
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(
        {
            "qr_type"    : type, 
            "id_details" : payload
        },
        status=status.HTTP_200_OK
    )
    


@api_view(['POST'])
def decrypt_qr_image(request : HttpRequest) -> Response :
    data = request.data
    
    try:
        image_str = data.pop("qr")
    except KeyError:
        return Response(
            {
                "error" : DRFErrors.InvalidPOSTBody,
                "details" : "Expected qr, got None instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        type, payload = read_qr_image(image_str).values()
    except Exception as err:
        return Response(
            {
                "error"   : DRFErrors.QRVerificationFailed,
                "details" : str(err)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if type == QRTypes.OpenLGUQR:
        if not Resident.objects.filter(uin=payload[169][75]).exists():
            return Response(
                {
                    "error"   : DRFErrors.DjangoUserDoesNotExist,
                    "details" : f"User {payload[169][75]} does not exist." 
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(
        { 
            "qr_type"    : type, 
            "id_details" : payload
        },
        status=status.HTTP_200_OK
    )
