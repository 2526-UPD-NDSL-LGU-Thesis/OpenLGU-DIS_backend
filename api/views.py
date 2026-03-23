'''
Django views for API.
'''

from qr_manager import verify_message, decrypt_message
from service.models import Service
from service.utils import claim_service
from residents.models import User
import base64
import io
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, JsonResponse, HttpResponse
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyzbar.pyzbar import decode
from mosip.models import MOSIPCollabUser, MOSIPException, start_otp
from io import BytesIO
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
        user = MOSIPCollabUser.verify_kyc(pcn=pcn, name_eng=name, dob=dob)
        return JsonResponse(user.__dict__, status=200)
    except MOSIPException:
        return JsonResponse({ "Authentication failed." }, status=400)
    

TEMPLATE_PATH = r'./residents/static/img/front.png'

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def digitalid(request : HttpRequest) -> JsonResponse :
    '''Generate Digital ID.'''

    NAME = request.data.get("userName")
    CARD_NUMBER_1  = request.data.get("philsysCardNumber")
    # CARD_NUMBER_2
    try:
        face_bytes = base64.b64decode(request.data.get("faceData").split(",")[1])
    except IndexError:
        face_bytes = base64.b64decode(request.data.get("faceData"))
    FACE = Image.open(BytesIO(face_bytes)).convert("RGBA")

    card = Image.open(TEMPLATE_PATH).convert("RGBA")
    
    WIDTH, HEIGHT = card.size
    draw = ImageDraw.Draw(card)

    # Define face box size
    face_width = int(WIDTH * 0.35)
    face_height = int(HEIGHT * 0.35)

    face = ImageOps.fit(FACE, (face_width, face_height), Image.Resampling.LANCZOS)

    # Optional: add rounded corners
    mask = Image.new("L", (face_width, face_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (face_width, face_height)],
        radius=30,
        fill=255
    )

    face.putalpha(mask)

    # Position face on left
    face_x = 40
    face_y = 300

    card.paste(face, (face_x, face_y), face)

    try:
        font_name = ImageFont.truetype("arialbd.ttf", 30)
        font_text = ImageFont.truetype("arial.ttf", 30)
    except:
        font_name = ImageFont.load_default(30)
        font_text = ImageFont.load_default(30)

    # -----------------------------
    # DRAW TEXT (RIGHT SIDE)
    # -----------------------------
    text_x = face_x + face_width + 25

    draw.text((text_x, 300), NAME, fill="black", font=font_name)
    draw.text((text_x, 380), "Card Number 1:", fill="black", font=font_text)
    draw.text((text_x, 420), CARD_NUMBER_1, fill="black", font=font_text)
    # draw.text((text_x, 530), f"Card Number 2:", fill="black", font=font_text)
    # draw.text((text_x, 570), CARD_NUMBER_2, fill="black", font=font_text)

    buffer = BytesIO()
    card.convert("RGB").save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer, content_type="image/png", status=200)


@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def start_verify_otp(request : HttpRequest) -> JsonResponse :
    """Starts the OTP Authentication process for a User.

    :param request: A request including the User's PCN from an authenticated account.
    :type request: HttpRequest
    :return: Returns the MOSIP OTP authentication transaction ID.
    :rtype: JsonResponse
    """
    pcn = request.data.get("pcn")

    try:
        txn = start_otp(pcn=pcn, phone_otp=True)
        return JsonResponse({ "txn": txn }, status=200)
    except MOSIPException:
        return JsonResponse({ "Authentication failed." }, status=400)

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def verify_otp(request : HttpRequest) -> JsonResponse :
    """Verify OTP Authentication.

    :param request: A request from an authenticated account.
    :type request: HttpRequest
    :return: Returns the requested User's information, or a fail otherwise.
    :rtype: JsonResponse
    """
    pcn = request.data.get("pcn")
    txn = request.data.get("txn")
    otp = request.data.get("otp")

    try:
        user = MOSIPCollabUser.verify_otp(pcn=pcn, txn_id=txn, otp=otp)
        return JsonResponse(user.__dict__, status=200)
    except MOSIPException:
        return JsonResponse({ "Authentication failed." }, status=400)

@api_view(['POST'])
# @authentication_classes([BasicAuthentication])
# @permission_classes([IsAuthenticated])
def authenticate_message(request : HttpRequest) -> JsonResponse :
    qr = request.data.get("qr")
    
    try:
        uncompressed_msg = zlib.decompress(qr)
        
        try:
            decrypted_msg = decrypt_message(uncompressed_msg)

                try:
                    verified_msg = verify_message(decrypted_msg)

                    cwt_msg = cbor2.loads(verified_msg)
                    claim_169 = cbor2.loads(cwt_msg[169])

                    payload = {
                        "iss" : cwt_msg[1],
                        "iat" : cwt_msg[6],
                        "pcn" : claim_169[1],
                        "img" : base64.b64encode(claim_169[16]).decode("utf-8"),
                        "imt" : claim_169[17],
                        "lid" : claim_169[99]
                    }
                    
                    return JsonResponse(
                        payload, status=200
                    )
                except:
                    return JsonResponse(
                        { "message" : "QR could not be verified" }, status=401
                    )
        except:
            return JsonResponse(
                { "message" : "QR could not be decrypted" }, status=401
            )
    except:
        return JsonResponse(
            { "message" : "QR could not be decompressed" }, status=401
        )


@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def claim(request : HttpRequest) -> JsonResponse :
    """Partnered Merchant claims a service for a User.

    :param request: A request from an authenticated account.
    :type request: HttpRequest
    :return: Returns a JsonResponse indicating a fail or success with the transaction.
    :rtype: JsonResponse
    """
    user_id = request.data.get("user_id")
    service_id = request.data.get("service_id")

    print(user_id)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse(
            { "error": "Resident not found" },
            status=404
        )
    
    if not user.verified:
        return JsonResponse(
            { "error": "Resident not verified" },
            status=403
        )
    
    try:
        service = Service.objects.get(id=service_id, active=True)
    except Service.DoesNotExist:
        return JsonResponse(
            { "error": "Service not found" },
            status=404
        )

    try:
        claim_service(user, service)
        return JsonResponse({ "Success" }, status=201)
    except:
        return JsonResponse({ "Failed to claim"}, status=400)

from pyzbar.pyzbar import decode
from PIL import Image
import zlib

@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def upload_qr(request) -> JsonResponse :
    qr_image = request.data.get("qr_image")

    img = Image.open(qr_image)
    decoded_objects = decode(img)

    try:
        b45_ = base45.b45decode(decoded_objects[0].data)
    except:
        return JsonResponse({ "Failed to decode QR" }, status=400)

    decompressed = zlib.decompress(b45_)

    result, payload = verify_message(decompressed)

    print(result)
    print(payload)

    if result:
        payload["face_data"] = base64.b64encode(payload["face_data"]).decode('utf-8')
        return JsonResponse(payload, status=201)
    else:
        return JsonResponse(payload, status=400)


@api_view(['GET'])
def ping(request) -> JsonResponse :
    return JsonResponse({ "message": "pong" }, status=201)