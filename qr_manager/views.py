"""
API views for QR Manager app.
"""


from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from residents.models import Resident
from .utils import read_qr, read_qr_image
from .classes import QRTypes
from .exceptions import DRFErrors


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
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

    uin = payload.get("uin")
    if type == QRTypes.OpenLGUQR:
        if not Resident.objects.filter(uin=uin).exists():
            return Response(
                {
                    "error"   : DRFErrors.DjangoUserDoesNotExist,
                    "details" : f"User {uin} does not exist." 
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
@permission_classes([IsAuthenticatedOrReadOnly])
def decrypt_qr_image(request : HttpRequest) -> Response :
    data = request.data
    
    
    image_str = data.get("qr")
    if not image_str:
        return Response(
            {
                "error" : DRFErrors.InvalidPOSTBody,
                "details" : "Expected 'qr', got None instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        

    try:
        qr_type, payload = read_qr_image(image_str).values()
    except Exception as err:
        return Response(
            {
                "error"   : DRFErrors.QRVerificationFailed,
                "details" : str(err)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if qr_type != QRTypes.OpenLGUQR:
        return Response(
            {
                "error"   : DRFErrors.InvalidQRType,
                "details" : f"Expected {QRTypes.OpenLGUQR}, got {qr_type} instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uin = payload.get("uin")
    if not Resident.objects.filter(uin=uin).exists():
        return Response(
            {
                "error"   : DRFErrors.ResidentDoesNotExist,
                "details" : f"User {uin} does not exist." 
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {
            "qr_type"    : qr_type, 
            "id_details" : payload
        },
        status=status.HTTP_200_OK
    )
