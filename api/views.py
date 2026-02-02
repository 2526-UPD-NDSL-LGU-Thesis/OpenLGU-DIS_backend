'''
Django views for API.
'''

import base64
import io
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, JsonResponse
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from PIL import Image
from pyzbar.pyzbar import decode
from mosip.models import MOSIPCollabUser

import cbor2
import base45

# Create your views here.
@csrf_exempt
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def read(request : HttpRequest) -> JsonResponse :
    '''Read QR image.'''
    b64image = request.data.get("qr_data")

    if b64image:
        image_data = base64.b64decode(b64image[22:])
        image = Image.open(io.BytesIO(image_data))
        
        try:
            # Reading Claim 169 QR
            qr_data = decode(image)[0].data.decode("utf-8")

            schema = qr_data[:3]

            if schema != "PH1":
                raise ValueError

            payload_b45 = qr_data[4:]
            decoded_b45 = base45.b45decode(payload_b45)
            decoded_cbor = cbor2.loads(decoded_b45)
            header, _, payload_b64, signature = decoded_cbor.value
            payload_data = cbor2.loads(payload_b64)

            payload_data[169]['img'] = None
            
            return JsonResponse(payload_data)
        except ValueError:
            # Reading Normal QR
            decoded_text = decode(image)[0].data.decode('utf-8')

            return JsonResponse(json.loads(decoded_text))
        
    return JsonResponse({ "error": "Upload the QR image using POST." }, status=400)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def verify(request : HttpRequest) -> JsonResponse :
    '''Verify User PCN.'''
    name = request.data.get("name")
    dob  = request.data.get("DOB")
    pcn  = request.data.get("PCN")

    try:
        user = MOSIPCollabUser.verify(id_=pcn, name_eng=name, dob=dob)
        return JsonResponse(user.__dict__, status=200)
    except:
        return JsonResponse({ "Authentication failed." }, status=400)