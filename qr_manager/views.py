"""
API views for QR Manager app.
"""


from django.http import HttpRequest, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status as HTTPStatus
import zlib

from .main import (
    sign_message, verify_message,
    encrypt_message, decrypt_message,
    sign_eddsa, verify_eddsa,
)
from .claim169 import CBORWebToken


@api_view(['POST'])
def decrypt_qr(request : HttpRequest) -> JsonResponse :
    data = request.data
    b45_qr = data.pop("qr")

    decompressed = zlib.decompress(b45_qr)

    status, payload =  verify_eddsa(decompressed)

    if not status:
        return JsonResponse(
            { "error" : "invalid_signature", "message" : "Key failed to validate signature" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )

    try:
        cwt = CBORWebToken.from_cbor(payload)
        return JsonResponse(
            cwt.model_dump(),
            status=HTTPStatus.HTTP_200_OK
        )
    except Exception as err:
        return JsonResponse(
            { 
                "error" : "invalid_cbor_structure",
                "message" : "Payload does not match with the current known structre.",
                "exception" : err 
            },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )
