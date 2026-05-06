"""
Class definitions for QR Manager.
"""

# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name


from strenum import StrEnum
from enum import auto


class QRTypes(StrEnum):
    PhilSysTemporaryQR  = auto()
    PhilSysPhysicalQR   = auto()
    eGovPHBackQR        = auto()
    OpenLGUQR           = auto()


class DRFErrors(StrEnum):
    InvalidPOSTBody        = auto()
    QRVerificationFailed   = auto()
    DjangoUserDoesNotExist = auto()
