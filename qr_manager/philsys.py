""" 
Parsing library for MOSIP QRs.
"""

from typing import Optional, Dict
import cbor2

from pycose.messages.sign1message import Sign1Message
import base45


def read_qr(qr_code : str) -> Optional[Dict] :
    b45_prefix = qr_code[:4]
    b45_payload = qr_code[4:]

    if b45_prefix != "PH1:":
        return

    b45_qr = base45.b45decode(b45_payload)

    signed_msg = Sign1Message.decode(b45_qr)

    payload = cbor2.loads(signed_msg)

    return payload
