"""
Exception definitions for Residents.
"""

# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name


from strenum import StrEnum
from enum import auto


class DRFErrors(StrEnum):
    InvalidPOSTBody        = auto()
