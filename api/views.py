'''
Django views for API.
'''

import base64
import io
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, JsonResponse
from rest_framework.decorators import api_view
from PIL import Image
from pyzbar.pyzbar import decode

import cbor2
import base45

# Create your views here.
@csrf_exempt
@api_view(['POST'])
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
        
    return JsonResponse({ "error": "Upload an image using POST." }, status=400)
