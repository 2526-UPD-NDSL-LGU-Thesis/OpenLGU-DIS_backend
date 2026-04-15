""" 
Parsing library for MOSIP QRs.
"""

from typing import Optional, Dict
import cbor2

from pycose.messages.sign1message import Sign1Message
import base45


def read_qr(qr_code : str) -> Optional[Dict] :
    if qr_code[:4] == "PH1:":
        prefix, content = qr_code[:4], qr_code[4:]

        b45_qr = base45.b45decode(content)

        # signed_msg = Sign1Message.decode(b45_qr)
        signed_message = cbor2.loads(b45_qr)

        # payload = cbor2.loads(signed_msg)
        payload = signed_message.value[2]
        
        cwt = cbor2.loads(payload)

        return cwt
    
    raise ValueError("QR not supported")
