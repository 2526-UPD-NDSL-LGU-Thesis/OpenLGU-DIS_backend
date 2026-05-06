""" 
Parsing library for QRs.
"""


from typing import Dict
from pycose.messages.sign1message import Sign1Message
from pyzbar import pyzbar
from io import BytesIO
from PIL import Image
import base45
import base64
import cbor2
import zlib


from .main import pycose_verify_message
from .classes import QRTypes


def to_base64_image(image_bytes : bytes) -> str :
    return base64.b64encode(image_bytes).decode()


def read_qr(qr_code : str) -> Dict :
    """Decodes information from supported QR codes.

    Args:
        qr_code (str): Base45-string of the QR code.

    Raises:
        ValueError: Invalid base45 string.
        ValueError: Invalid Sign1Message object.
        ValueError: Invalid CBOR object.

    Returns:
        Dict: Type of QR code and payload.
    """
    #TODO: Handle eGovPH QRs
    if qr_code[:4] == "PH1:":
        prefix, content = qr_code[:4], qr_code[4:]

        try:
            b45_qr = base45.b45decode(content)
        except Exception as err:
            raise ValueError("QR code is not a valid base45 encoding.") from err

        try:
            signed_msg = Sign1Message.decode(b45_qr)
        except Exception as err:
            raise ValueError("Message is not a valid Sign1Message.") from err
        
        try:
            payload = cbor2.loads(signed_msg.payload)
        except Exception as err:
            raise ValueError("Payload is not a valid CBOR object.") from err

        try:
            payload[169]['img'] = to_base64_image(payload[169]['img'])
        except KeyError:
            pass

        return {
            "type"    : QRTypes.PhilSysTemporaryQR,
            "content" :  payload
        }
    else:
        try:
            b45_qr = base45.b45decode(qr_code)
        except Exception as err:
            raise ValueError("QR code is not a valid base45 encoding.") from err

        try:
            decompressed_qr = zlib.decompress(b45_qr)
        except Exception as err:
            raise ValueError("Content is not decompressed using zlib.") from err

        try:
            payload = pycose_verify_message(decompressed_qr)
        except Exception as err:
            raise ValueError(f"Failed to verify QR code: {err}") from err

        try: 
            payload[169][62] = to_base64_image(payload[169][62])
        except KeyError:
            pass
        
        return {
            "type"    : QRTypes.OpenLGUQR,
            "content" : payload
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
        raise ValueError(f"{err}")

# def generate_qr(uin : str, user : MOSIPUser) :
#     claim169 = user.to_claim169
#     claim169[99] = uin

#     cwt = {
#         1   : "OpenLGU",
#         2   : int(datetime.now().timestamp()),
#         169 : claim169
#     }

#     cbor_cwt = cbor2.dumps(cwt)
    # pass
