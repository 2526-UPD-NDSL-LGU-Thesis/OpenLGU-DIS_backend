"""
Exception definitions for Service.
"""


# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name


from strenum import StrEnum
from enum import auto


class DRFErrors(StrEnum):
    InvalidPOSTBody        = auto()
    InvalidQRType          = auto()
    QRVerificationFailed   = auto()
    ResidentDoesNotExist   = auto()
    ServiceDoesNotExist    = auto()
    MOSIPMissingValues     = auto()
    MOSIPAuthFailed        = auto()
