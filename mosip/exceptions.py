"""
Error classes for MOSIP module.
"""


# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name


from strenum import StrEnum
from enum import auto


class MOSIPException(Exception):
    """Base class for MOSIP errors."""
    def __init__(self, *args):
        super().__init__(*args)


class MOSIPParsingError(MOSIPException):
    """Errors from parsing demographic data."""


class MOSIPMissingFieldError(MOSIPException):
    """Errors from missing required field/s in demograpic data."""


class MOSIPLanguageError(MOSIPException):
    """Errors from using unsupported language in transactions."""


class DRFErrors(StrEnum):
    MOSIPConnectionFailed    = auto()


#TODO:
'''
- What failed?
- Where did it fail?
- Why did it fail?
- What data caused it?
'''