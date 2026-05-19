""" 
Parsing library for QRs.
"""


from typing import Any, Dict
from pyzbar import pyzbar
from io import BytesIO
from PIL import Image
from datetime import datetime
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
            pass
    
        obj = cbor2.loads(raw)

        return True
    except Exception:
        return False


def detect_qr_type(qr_code : str) -> QRTypes :
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

    Raises:
        ValueError: Invalid image bytes.
        ValueError: Failed to read QR code.

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


def generate_qr(**kwargs) :
    required_headers = [
        "first_name", "last_name", "gender", "birthdate", "address",
        "phone", "pcn", "uin"
    ]

    missing = [header for header in required_headers if header not in kwargs]

    if missing:
        raise ValueError(f"Missing required headers: {', '.join(missing)}")

    claim169 = {
        1  : kwargs["pcn"],
        # 2 : version
        # 3 : language ISO
        # 4 : full name
        5  : kwargs["first_name"],
        # 6 : kwargs["middle_name"],
        7  : kwargs["last_name"],
        8  : kwargs["birthdate"],
        9  : ( 
            1 if kwargs["gender"] == "Male" 
            else 2 if kwargs["gender"] == "Female"
            else 3
        ),
        10 : kwargs["address"],
        # 11 : kwargs["email"],
        12 : kwargs["phone"],
        # 13 : nationality
        # 14 : marital status
        # 15 : Guardian
        # 16 : image depreciated
        # 17 : image type depreciated
        # 18 : fingers
        # 19 : name in secondary language
        # 20 : language ISO
        # 21 : location code
        # 22 : legal status
        # 23 : country of issuance
        # 24-29 : unassigned
        # 50-59 : fingers
        # 60-61 : eyes
        # 62 : kwargs["face"],
        # 63-64 : palms
        # 65 : voice
        # 66-74 : unassigned (for future biometrics)
        75 : kwargs["uin"]
        # 75-99 : unassigned
    }
    
    cwt = {
        1   : "ndsl.openlgu.com.ph/",
        2   : str(int(datetime.now().timestamp())),
        169 : claim169
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
