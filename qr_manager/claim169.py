"""
Claim169 generator for OpenLGU.
"""

from typing import Optional, Self

from pydantic import BaseModel, Field, AliasChoices, model_validator
import cbor2


class Claim169(BaseModel):
    id : str = Field(validation_alias=AliasChoices("id", "1"))
    version : str = Field(validation_alias=AliasChoices("version", "2"))
    language : str = Field(validation_alias=AliasChoices("language", "3"))
    full_name : str = Field(validation_alias=AliasChoices("full_name", "4"))
    # 5
    # 6
    # 7
    dob : str = Field(validation_alias=AliasChoices("dob", "8"))
    gender : str = Field(validation_alias=AliasChoices("gender", "9"))
    location : str = Field(validation_alias=AliasChoices("location", "10"))
    email : str = Field(validation_alias=AliasChoices("email", "11"))
    phone : str = Field(validation_alias=AliasChoices("phone", "12"))
    # 13
    # 14
    # 15
    face : str = Field(validation_alias=AliasChoices("face", "16"))
    image_format : int = Field(validation_alias=AliasChoices("image_format", "17"))
    # 18
    # 19
    # 20
    # 21
    # 22
    # 23
    # 24 - 49
    # 50 - 65
    # 66 - 74
    # 75 - 99
    local_id : str = Field(validation_alias=AliasChoices("local_id", "99"))

    @model_validator(mode="before")
    def convert_int_keys(cls, data):
        # Handles your original dict with int keys
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items()}
        return data


class CBORWebToken(BaseModel):
    """CBOR Web Token (CWT) structure based on the Internet Assigned Numbers Authority \
    (IANA) CWT Registry, as suggested by MOSIP's 169 - QR Code Specifications.

    For more information, see the documentations:
    - https://www.iana.org/assignments/cwt/cwt.xhtml
    - https://docs.mosip.io/1.2.0/readme/standards-and-specifications/mosip-standards/169-qr-code-specification

    Attributes:
        iss (str): Issuer
        iat (int): Issued at (in unix timestamp)
        identity-data (Claim169): User information 
    """
    iss : str = Field(validation_alias=AliasChoices("iss", "1"))
    iat : int = Field(validation_alias=AliasChoices("iat", "6"))
    identity_data : Optional[Claim169] = Field(
        default=None,
        validation_alias=AliasChoices("identity_data", "169")
    )

    @model_validator(mode="before")
    def convert_int_keys(cls, data):
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items()}
        return data
    
    @classmethod
    def from_cbor(cls, cbor : bytes) -> Self :
        cbor_data = cbor2.loads(cbor)

        return cls.model_validate(**cbor_data)
