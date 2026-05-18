""" 
Parsing library for QRs.
"""


from typing import Dict
from pycose.messages.sign1message import Sign1Message
from pyzbar import pyzbar
from io import BytesIO
from PIL import Image
from datetime import datetime
import base45
import base64
import cbor2
import qrcode
import zlib


from .main import pycose_sign_message, pycose_verify_message
from .classes import QRTypes


def to_base64_image(image_bytes : bytes) -> str :
    return base64.b64encode(image_bytes).decode()


def parse_id_details(payload, qr_type : QRTypes):
    if qr_type == QRTypes.OpenLGUQR:
        cwt = payload
        claim169 = cwt[169]

        return {
            "issuer"     : cwt[1], 
            "issued_at"  : cwt[2],
            "pcn"        : claim169[1],
            "version"    : claim169[2],
            "first_name" : claim169[4],
            "middle_name": claim169[5],
            "last_name"  : claim169[6],
            "suffix_name": claim169[7],
            "dob"        : claim169[8],
            "pob"        : claim169[9],
            "gender"     : ( 
                "Male" if claim169[10] == 1
                else "Female" if claim169[10] == 2
                else "Others"
            ),
            "marital_status" : claim169[14],
            "blood_type"     : claim169[16],
            "best_fingers"   : claim169[18],
            "face"           : claim169[62],
            "uin"            : claim169[75]
        }
    
    if qr_type == QRTypes.PhilSysTemporaryQR:
        cwt = payload
        claim169 = cwt[169]
        biographic = claim169["sb"]

        return {
            "issuer_country"    : cwt[1], 
            "issued_at_unix"    : cwt[6],
            "confirmation"      : cwt[8],
            "issued_at"         : claim169["d"],
            "issuer"            : claim169["i"],
            "gender"            : biographic["s"],
            "best_fingers"      : biographic["BF"].strip("[]").split(","),
            "first_name"        : biographic["fn"],
            "last_name"         : biographic["ln"],
            "middle_name"       : biographic["mn"],
            "suffix_name"       : biographic["sf"],
            "dob"               : biographic["DOB"],
            "pcn"               : biographic["PCN"],
            "pob"               : biographic["POB"],
            "img"               : claim169["img"]
        }
        



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
            "type"       : QRTypes.PhilSysTemporaryQR,
            "id_details" :  parse_id_details(payload, QRTypes.PhilSysTemporaryQR)
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
            "type"       : QRTypes.OpenLGUQR,
            "id_details" : parse_id_details(payload, QRTypes.OpenLGUQR)
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
        "phone", "face", "pcn", "uin"
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
        62 : kwargs["face"],
        # 63-64 : palms
        # 65 : voice
        # 66-74 : unassigned (for future biometrics)
        75 : kwargs["uin"]
        # 75-99 : unassigned
    }
    
    cwt = {
        1   : "OpenLGU",
        2   : str(int(datetime.now().timestamp())),
        169 : claim169
    }

    cbor_cwt = cbor2.dump(cwt)

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
