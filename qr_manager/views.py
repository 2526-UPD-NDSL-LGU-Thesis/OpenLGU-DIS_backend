"""
API views for QR Manager app.
"""


from django.http import HttpRequest
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status

from .main import validate_qr
from residents.models import Resident


@api_view(['POST'])
def decrypt_qr(request : HttpRequest) -> Response :
    data = request.data
    try:
        b45_qr = data.pop("qr")
    except KeyError:
        return Response(
            {
                "error" : "error_random_qr",
                "message" : "Invalid POST body. Expected 'qr', got none instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    _status, payload = validate_qr(b45_qr)

    if not Resident.objects.filter(uin=payload[169][75]).exists():
        return Response(
            { "error" : "User does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )

    if _status:
        return Response(
            { "id_details" : payload },
            status=status.HTTP_200_OK
        )

    return Response(
        payload,
        status=status.HTTP_400_BAD_REQUEST
    )
