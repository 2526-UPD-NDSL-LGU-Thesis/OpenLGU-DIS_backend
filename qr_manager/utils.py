""" 
Parsing library for QRs.
"""

from typing import Optional, Dict
import cbor2

import base45

from mosip import MOSIPUser


def read_qr(qr_code : str) -> Optional[Dict] :
    """Decodes information from supported QRs.

    Args:
        qr_code (str): Base45-decoded string of the QR. 

    Raises:
        ValueError: If QR code is not a supported QR.

    Returns:
        Optional[Dict]: Payload inside the QR.
    """
    if qr_code[:4] == "PH1:":
        prefix, content = qr_code[:4], qr_code[4:]

        b45_qr = base45.b45decode(content)

        # signed_msg = Sign1Message.decode(b45_qr)
        signed_message = cbor2.loads(b45_qr)

        # payload = cbor2.loads(signed_msg)
        payload = signed_message.value[2]
        
        data = cbor2.loads(payload)
        data["type"] = "claim169"

        return data
    
    raise ValueError("QR not supported")


def read_qr_image():
    pass


def generate_qr(uin : str, user : MOSIPUser) :
    claim169 = user.to_claim169
    claim169[99] = uin

    cwt = {
        1   : "OpenLGU",
        2   : int(datetime.now().timestamp()),
        169 : claim169
    }

    cbor_cwt = cbor2.dumps(cwt)
    #TODO: Revert to COSE message
