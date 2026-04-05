"""
Claim169 generator for OpenLGU.
"""

from dataclasses import dataclass
from typing import Dict

@dataclass
class Claim169:
    """CBOR Web Token (CWT) structure based on the Internet Assigned Numbers Authority \
    (IANA) CWT Registry, as suggested by MOSIP's 169 - QR Code Specifications.

    For more information, see the documentations:
    - https://www.iana.org/assignments/cwt/cwt.xhtml
    - https://docs.mosip.io/1.2.0/readme/standards-and-specifications/mosip-standards/169-qr-code-specification

    Attributes:
        iss (str): Issuer
        iat (int): Issued at (in unix timestamp)
        identity-data : 
    """
    iss : str
    iat : int
    identity_data : Dict
