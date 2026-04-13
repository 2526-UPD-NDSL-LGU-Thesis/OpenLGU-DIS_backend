"""
API views for QR Manager app.
"""


from django.http import HttpRequest, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework import status as HTTPStatus

from .main import validate_qr


@api_view(['POST'])
def decrypt_qr(request : HttpRequest) -> JsonResponse :
    data = request.data
    b45_qr = data.pop("qr")

    status, payload = validate_qr(b45_qr)

    if status:
        return JsonResponse(
            payload,
            status=HTTPStatus.HTTP_200_OK
        )

    return JsonResponse(
        payload,
        status=HTTPStatus.HTTP_400_BAD_REQUEST
    )
