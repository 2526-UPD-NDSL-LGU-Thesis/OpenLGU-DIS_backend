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
    """Decodes information from supported QRs.

    Args:
        qr_code (str): Base45-decoded string of the QR. 

    Raises:
        ValueError: If QR code is not a supported QR.

    Returns:
        Optional[Dict]: Payload inside the QR.
    """
    #TODO: Handle eGovPH QRs
    if qr_code[:4] == "PH1:":
        prefix, content = qr_code[:4], qr_code[4:]

        b45_qr = base45.b45decode(content)

        signed_msg = Sign1Message.decode(b45_qr)
        
        payload = cbor2.loads(signed_msg.payload)

        payload[169]['img'] = to_base64_image(payload[169]['img'])

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
            payload[169][62] = to_base64_image(payload[169][62])
            return {
                "type"    : QRTypes.OpenLGUQR,
                "content" : payload
            }
        except Exception as err:
            raise ValueError(f"Failed to verify QR code: {err}") from err


def read_qr_image(b64_image : str) -> Dict :
    try:
        image_bytes = base64.b64decode(b64_image)
        image = Image.open(BytesIO(image_bytes))
    except Exception as err:
        raise ValueError("Failed to read image.") from err
    
    qr_code = pyzbar.decode(image)[0].data.decode()
    if qr_code:
        return read_qr(qr_code)
    else:
        raise ValueError("Failed to decode QR code from image.")

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
