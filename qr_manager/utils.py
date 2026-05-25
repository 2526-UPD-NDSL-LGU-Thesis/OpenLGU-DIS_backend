""" 
Parsing library for QRs.
"""


from typing import Any, Dict
from datetime import datetime
from django.conf import settings
from io import BytesIO
from PIL import Image, ImageEnhance
from pyzbar import pyzbar
import mediapipe as mp
import numpy as np
import base45
import base64
import cbor2
import json
import qrcode
import zlib


from .main import pycose_sign_message
from .classes import QRTypes
from .decoders import (
    decode_philsys_temporary_qr, decode_philsys_physical_qr,
    decode_egovph_front_qr, decode_egovph_back_qr,
    decode_openlgu_qr
)
from .face_landmarker import MediaPipeFaceLandMarker

mp_landmarker = MediaPipeFaceLandMarker()


def _to_base64_image(image_bytes : bytes) -> str :
    return base64.b64encode(image_bytes).decode()


def _detect_json_schema(qr_code : str) -> QRTypes :
    try:
        payload = json.loads(qr_code)
    except Exception as err:
        raise ValueError("QR code is not a valid JSON object.") from err

    if all(key in payload for key in [
        "p", "v", "z"
    ]):
        return QRTypes.eGovPHBackQR
    
    if all(key in payload for key in [
        "DateIssued", "Issuer", "alg", "signature", "subject"
    ]):
        return QRTypes.PhilSysPhysicalQR

    raise ValueError("QR code is not a supported JSON-encoded format.")


def _check_claim169_cwt(qr_code : str) -> bool :
    try:
        raw = base45.b45decode(qr_code)

        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            return False
    
        obj = cbor2.loads(raw)

        return True
    except Exception:
        return False


def crop_face_image_by_landmarks(landmarker, image_bytes : bytes,
                                 margin : int = 0) -> bytes :
    """Crop face image based on face landmarks.

    Args:
        landmarker (_type_): MediaPipe Landmarker model.
        image_bytes (bytes): Face image bytes.
        margin (int, optional): Margins around cropped face.

    Returns:
        bytes: Cropped face image in WEBP bytes.
    """
    img_pil = Image.open(BytesIO(image_bytes)).convert("RGB")

    img_np = np.array(img_pil)

    img_mp = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=img_np
    )

    face_landmarker_result = landmarker.detect(img_mp)

    # Get width and height
    width, height = img_pil.size

    # Extract landmarks (from the first detected face)
    landmarks = face_landmarker_result.face_landmarks[0]

    # Convert normalized landmarks to pixel coordinates
    points = np.array([[int(l.x * width), int(l.y * height)] for l in landmarks])

    # Compute bounding box (min/max)
    x_min, y_min = np.min(points, axis=0)
    x_max, y_max = np.max(points, axis=0)

    # Add a small margin
    x_min = max(x_min - margin, 0)
    y_min = max(y_min - margin, 0)
    x_max = min(x_max + margin, width)
    y_max = min(y_max + margin, height)

    # Compute width and height of the box
    box_w = x_max - x_min
    box_h = y_max - y_min

    # Make it square:
    if box_w > box_h:
        # If wider than tall — expand height equally
        diff = box_w - box_h
        y_min = max(y_min - diff // 2, 0)
        y_max = min(y_max + diff // 2, height)
    elif box_h > box_w:
        # If taller than wide — center vertically
        diff = box_h - box_w
        y_min = max(y_min + diff // 2, 0)
        y_max = min(y_max - diff // 2, height)

    # Crop image
    img_crop = img_pil.crop((x_min, y_min, x_max, y_max))

    buffer = BytesIO()
    img_crop.save(buffer, format="PNG")

    return buffer.getvalue()


def process_image(image_bytes : str) -> bytes :
    """Process image for QR code embedding.

    Args:
        image_bytes (str): Face image bytes in str.

    Returns:
        bytes: Processed face image in WEBP bytes.
    """
    image_bytes = base64.b64decode(image_bytes)

    try:
        landmarker = mp_landmarker.get_detector()
        image_bytes = crop_face_image_by_landmarks(landmarker, image_bytes)
    except RuntimeError:
        pass

    img_pil = Image.open(BytesIO(image_bytes))

    # Convert to Black and White
    img_pil = img_pil.convert("L")
    
    # Resize Image
    img_pil = img_pil.resize((45, 45), Image.LANCZOS)

    # Sharpen image
    img_pil = ImageEnhance.Sharpness(img_pil)
    img_pil = img_pil.enhance(1.5)

    # Adjust contrast
    img_pil = ImageEnhance.Contrast(img_pil)
    img_pil = img_pil.enhance(1.1)

    buffer = BytesIO()
    img_pil.save(buffer, format="WEBP", quality=20, method=6, optimize=True)

    return buffer.getvalue()


def detect_qr_type(qr_code : str) -> QRTypes :
    """Detects the type of the QR code based on encoding, format, and structure.

    Args:
        qr_code (str): Base45-string of the QR code.

    Returns:
        QRTypes: Type of QR code.
    """
    if qr_code.startswith("PH1:"):
        return QRTypes.PhilSysTemporaryQR
    
    if len(qr_code) == 16 and qr_code.isdigit:
        return QRTypes.eGovPHFrontQR
    
    if qr_code.startswith("{"):
        return _detect_json_schema(qr_code)
    
    if _check_claim169_cwt(qr_code):
        return QRTypes.OpenLGUQR
    
    raise ValueError("QR code is not a supported QR code format.")


def read_qr(qr_code : str) -> Dict[str, Any] :
    """Returns information from supported QR codes.

    Args:
        qr_code (str): Base45-string of the QR code.

    Returns:
        Dict: Type of QR code and a standardized payload.
    """
    qr_code = qr_code.strip()

    qr_type = detect_qr_type(qr_code)

    id_details = None
    match qr_type:
        case QRTypes.PhilSysPhysicalQR:
            id_details = decode_philsys_physical_qr(qr_code)
        
        case QRTypes.PhilSysTemporaryQR:
            id_details = decode_philsys_temporary_qr(qr_code)
        
        case QRTypes.eGovPHFrontQR:
            id_details = decode_egovph_front_qr(qr_code)

        case QRTypes.eGovPHBackQR:
            id_details = decode_egovph_back_qr(qr_code)

        case QRTypes.OpenLGUQR:
            id_details = decode_openlgu_qr(qr_code)

        case _:
            raise ValueError(f"Current implementation does not have a decoder for {qr_type}.")
    
    return {
        "qr_type" : qr_type,
        "id_details" : id_details
    }


def read_qr_image(b64_image : str) -> Dict :
    """Decodes information from supported QR code image.

    Args:
        b64_image (str): Base64-encoded string of an image.

    Returns:
        Dict: Type of QR code and payload.
    """
    try:
        image_bytes = base64.b64decode(b64_image)
        image = Image.open(BytesIO(image_bytes))
    except Exception as err:
        raise ValueError("Failed to generate image from bytes.") from err
    
    qr_code = pyzbar.decode(image)[0].data.decode()
    try:
        return read_qr(qr_code)
    except Exception as err:
        raise ValueError(f"{err}") from err


def generate_qr(**kwargs) -> bytes :
    """Generate QR code based on MOSIP Claim 169 version 1.2.1.

    Returns:
        bytes: QR code image in raw bytes.
    """
    required_headers = [
        "pcn", "date_of_birth", "address", "face_image", "uin"
    ]

    name_headers = [
        "first_name", "last_name", "middle_name", "suffix_name"
    ]

    missing = [
        header
        for header in required_headers
        if not kwargs.get(header)
    ]

    if not any([
        all(header in kwargs for header in name_headers),
        "full_name" in kwargs
    ]):
        missing.append("name")

    if missing:
        raise ValueError(f"Missing required headers: {', '.join(missing)}")

    face_image = kwargs.get("face_image")
    face_bytes = b''
    if not face_image is None:
        face_bytes = process_image(face_image)

    claim169 = {
        1  : kwargs.get("pcn"),
        2  : kwargs.get("version", settings.VERSION),
        3  : kwargs.get("language", settings.DEFAULT_LANGUAGE_ISO),
        4  : kwargs.get("full_name"),
        5  : kwargs.get("first_name"),
        6  : kwargs.get("middle_name"),
        7  : kwargs.get("last_name"),
        8  : kwargs.get("date_of_birth"),
        9  : (
            1 if kwargs.get("gender") == "Male"
            else 2 if kwargs.get("gender") == "Female"
            else 3 if kwargs.get("gender") == "Others"
            else None
        ),
        10 : kwargs.get("address"),
        11 : kwargs.get("email_id"),
        12 : kwargs.get("phone_number"),
        13 : kwargs.get("nationality"),
        14 : (
            1 if kwargs.get("marital_status") == "Unmarried"
            else 2 if kwargs.get("marital_status") == "Married"
            else 3 if kwargs.get("marital_status") == "Divorced"
            else None
        ),
        # 15 : kwargs.get("guardian"),
        # 16 : image depreciated
        # 17 : image type depreciated
        18 : kwargs.get("best_fingers"),
        # 19 : kwargs.get("full_name_secondary"),
        # 20 : kwargs.get("language_secondary"),
        # 21 : kwargs.get("location_code"),
        # 22 : kwargs.get("legal_status"),
        23 : kwargs.get("issuing_country", settings.DEFAULT_COUNTRY_ISO),
        # 24-49 : For future - For Demographic Data attributes
        50 : kwargs.get("right_thumb"),
        51 : kwargs.get("right_pointer_finger"),
        52 : kwargs.get("right_middle_finger"),
        53 : kwargs.get("right_ring_finger"),
        54 : kwargs.get("right_little_finger"),
        55 : kwargs.get("left_thumb")  ,
        56 : kwargs.get("left_pointer_finger"),
        57 : kwargs.get("left_middle_finger"),
        58 : kwargs.get("left_ring_finger"),
        59 : kwargs.get("left_little_finger"),
        60 : kwargs.get("right_iris"),
        61 : kwargs.get("left_iris"),
        62 : face_bytes,
        63 : kwargs.get("right_palm_print"),
        64 : kwargs.get("left_palm_print"),
        65 : kwargs.get("voice"),
        # 66-74 : For future - For Biometrics Data attributes
        # 75-99 : For future - For any other data
        75 : kwargs.get("uin")
    }

    cleaned_claim169 = {
        k : v for k, v in claim169.items()
        if v is not None
    }

    cwt = {
        1   : "ndsl.openlgu.com.ph",
        6   : int(datetime.now().timestamp()),
        169 : cleaned_claim169
    }

    cbor_cwt = cbor2.dumps(cwt)

    signed_message = pycose_sign_message(cbor_cwt)

    compressed_message = zlib.compress(signed_message)

    b45_message = base45.b45encode(compressed_message)

    qr = qrcode.QRCode()
    qr.add_data(b45_message.decode())
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    return image_bytes
