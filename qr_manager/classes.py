"""
Class definitions for QR Manager.
"""

# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name


from dataclasses import dataclass
from enum import auto
from strenum import StrEnum
from typing import Dict, List, Optional

class QRTypes(StrEnum):
    PhilSysTemporaryQR  = auto()
    PhilSysPhysicalQR   = auto()
    eGovPHBackQR        = auto()
    eGovPHFrontQR       = auto()
    OpenLGUQR           = auto()


@dataclass
class QRDetails:
    token_issuer : Optional[str] = None
    token_issued_at : Optional[int] = None
    token_confirmation : Optional[Dict[int, str]] = None
    algorithm : Optional[str] = None
    signature : Optional[str] = None

    issuer : Optional[str] = None
    issued_at : Optional[str] = None
    issuing_country : Optional[str] = None

    pcn : Optional[str] = None
    uin : Optional[str] = None
    egov_digital_id : Optional[str] = None

    version : Optional[str] = None
    language : Optional[str] = None

    full_name : Optional[str] = None
    first_name : Optional[str] = None
    middle_name : Optional[str] = None
    last_name : Optional[str] = None
    suffix_name : Optional[str] = None

    bloodtype : Optional[str] = None
    gender : Optional[str] = None
    date_of_birth : Optional[str] = None
    place_of_birth : Optional[str] = None
    address : Optional[str] = None

    email_id : Optional[str] = None
    phone_number : Optional[str] = None

    nationality : Optional[str] = None
    marital_status : Optional[str] = None

    best_fingers : Optional[List[int | None]] = None
    face_image : Optional[str] = None
