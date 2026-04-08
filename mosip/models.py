"""
Pydantic Models for MOSIP Collab user.
"""

import base64
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from typing import Self, Dict, List, Optional

from django.conf import settings
from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue
from mosip_auth_sdk.models import DemographicsModel
from pydantic import BaseModel, Field, AliasChoices
from PIL import Image
from requests.models import Response

from .exceptions import (
    MOSIPException, MOSIPParsingError,
    MOSIPMissingFieldError,
    MOSIPLanguageError
)

from .authenticator import MOSIPAuthManager

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
    
manager = MOSIPAuthManager()


def _to_demographic_data(**kwargs) -> DemographicsModel:
    """Convert demographic kwargs into a `DemographicsModel` for MOSIP Authentication.
    
    Args:
        **kwargs: Arbitrary keyword arguments representing demographic data. 
            Expected keys include:
            - age (str): Age of the individual.
            - dob (str): Date of birth in ISO format (YYYY-MM-DD).
            - name / name_<lang> (list[dict[str, str]]): Names in various languages.
            - dob_type / dob_type_<lang> (str): Type of date of birth.
            - gender / gender_<lang> (str): Gender information.
            - phone_number (str): Contact phone number.
            - email_id (str): Email address.
            - address_line1 / address_line1_<lang> (str)
            - address_line2 / address_line2_<lang> (str)
            - address_line3 / address_line3_<lang> (str)
            - location1 / location1_<lang> (str)
            - location2 / location2_<lang> (str)
            - location3 / location3_<lang> (str)
            - postal_code (str)
            - full_address / full_address_<lang> (str)
            - metadata (dict): Additional metadata for the individual.
    """

    if not kwargs:
        raise MOSIPMissingFieldError("At least one demographic field is required")

    def _identity(value: str, language: str = settings.DEFAULT_LANGUAGE_ISO):
        return [{"language": language, "value": value}]

    def _parse_language(key: str, parts_expected: int):
        lang = None

        try:
            parts = key.split("_")
            if len(parts) == parts_expected:
                lang = parts[-1]
                Lang(pt3=lang)
                return lang
        except InvalidLanguageValue as err:
            raise MOSIPLanguageError(
                f"{lang} from {key} is not a valid ISO639-3 language code"
            ) from err
        return settings.DEFAULT_LANGUAGE_ISO

    def _parse_dob(value):
        if isinstance(value, datetime):
            return value.strftime("%Y/%m/%d")

        if isinstance(value, str):
            for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime("%Y/%m/%d")
                except ValueError:
                    continue

        raise MOSIPParsingError(
            f"Invalid DOB format: {value}. Expected YYYY/MM/DD or YYYY-MM-DD"
        )

    def _validate_phone(value: str):
        if value.isdigit() and len(value) == 11:
            return value
        if value.startswith("+63") and len(value) == 13 and value[1:].isdigit():
            return value
        raise MOSIPParsingError(f"Invalid phone number: {value}")

    data: dict = {}

    for raw_key, value in kwargs.items():
        key = raw_key.lower()

        match key:
            case "age":
                try:
                    data["age"] = str(int(value))
                except ValueError as err:
                    raise MOSIPParsingError("Age must be an integer") from err

            case "dob":
                data["dob"] = _parse_dob(value)

            case "phone_number":
                data["phone_number"] = _validate_phone(value)

            case "email_id":
                data["email_id"] = value.lower()

            case "postal_code":
                if value.isdigit() and len(value) == 4:
                    data["postal_code"] = value
                else:
                    raise MOSIPParsingError("Postal code must be a 4-digit number")

            case _ if key.startswith(("name", "gender", "dob_type")):
                lang = _parse_language(key, parts_expected=2 if "dob_type" not in key else 3)
                field = key.split("_")[0] if "dob_type" not in key else "dob_type"
                data[field] = _identity(value, lang)

            case _ if key.startswith((
                "address_line1", "address_line2", "address_line3",
                "location1", "location2", "location3",
                "full_address"
            )):
                parts = key.split("_")
                field = "_".join(parts[:2]) if "address" in key else parts[0]
                lang = _parse_language(key, parts_expected=len(parts))
                data[field] = _identity(value, lang)

            case _:
                raise MOSIPParsingError(f"Unsupported parameter: {raw_key}")

    if not data:
        raise MOSIPMissingFieldError("No valid demographic data provided")

    return DemographicsModel(**data)


def decode_face(face_b64 : str) -> str :
    """Decode face image bytes from MOSIP response body to Base64 string."""
    face_bytes = base64.b64decode(face_b64)[73:]
    face_img = Image.open(BytesIO(face_bytes))
    try:
        face_img.load()
    except Exception as err:
        raise MOSIPException("Failed to decode image") from err

    return base64.b64encode(face_bytes).decode("utf-8")

class MOSIPUser(BaseModel):
    """User class from MOSIP Authentication SDK's response body.

    Interfaces the decrypted response body of a successful authentication transaction. \
    Otherwise, raise an `ExceptionGroup` of all errors from response body when authentication \
    fails.

    For more information regarding the SDK, see the documentation:
    https://docs.mosip.io/1.2.0/id-lifecycle-management/identity-verification/id-authentication-services/mosip-authentication-sdk
    
    Attributes:
        uid (str): User's unique identifier
        name (dict[str, str]): User's name in different locales (e.g., 'eng', 'fil')
        gender (dict[str, str]): User's gender in different locales
        dob (str): User's date of birth
        location1 (dict[str, str]): User's location fields in different locales
        phone (str): Phone number
        email (str): Email address
        face (bytes): Base64-encoded face image

    Raises:
        MOSIPParsingError: Errors encountered during demographic data cleaning
        MOSIPResponseError: Errors encountered during authentication
    """
    uid        : Optional[str] = Field(default=None)
    name       : Dict[str, str] = Field(default_factory=dict)
    gender     : Dict[str, str] = Field(default_factory=dict)
    dob        : str
    location1  : Dict[str, str] = Field(default_factory=dict)
    phone      : str
    email      : str
    face       : str

    @classmethod
    def from_response(cls, response : Response) -> Self :
        """Decrypt User info from MOSIP response."""
        response = response.json()

        authenticator = manager.get_authenticator()
        mosip_user = defaultdict(dict)

        decrypted_response = authenticator.decrypt_response(response)

        for key, value in decrypted_response.items():
            try:
                key_var, key_lang = key.split("_")

                match key_var:
                    # TODO: Add other demographics
                    case "name":
                        mosip_user["name"][key_lang] = value
                    case "gender":
                        mosip_user["gender"][key_lang] = value
                    case "location1":
                        mosip_user["location1"][key_lang] = value
                    case _:
                        raise Warning(f"Unsupported parameter: {key_var}")
            except ValueError:
                if key == "face":
                    mosip_user["face"] = decode_face(decrypted_response["face"])
                else:
                    mosip_user[key] = value
        
        return cls(**mosip_user)

    @property
    def info(self) -> Dict[str, str | int] :
        """
        User's demographic information without the face data.
        """

        return {
            key: value for key, value in self.__dict__.items()
            if key != "face"
        }
    
    @property
    def to_claim169(self) -> Dict[int, any] :
        default_lang = settings.DEFAULT_LANGUAGE_ISO
        claim169 = {
            1 : self.uid,
            2 : settings.VERSION,
            3 : default_lang,
            4 : self.name[default_lang],
            # TODO: Is there a way to know the first/middle/last name from full name?
            # 5 : first name
            # 6 : middle name
            # 7 : last name
            8 : self.dob,
            9 : self.gender[default_lang],
            10 : self.location1[default_lang],
            11 : self.email,
            12 : self.phone,
            # 13 : nationality (unsupported)
            # 14 : marital status (unsupported)
            # 15 : guardian (unsupported)
            16 : self.face,
            17 : 2,                                 # JPEG
            # 18 : best quality fingers (unsupported)
            # 19 : full name in secondary language (unsupported)
            # 20 : secondary language (unsupported)
            # 21 : location code (unsupported)
            # 22 : legal status (unsupported)
            # 23 : country of issuance (unsupported)
            # 24 - 49 : unassigned
            # 50 - 65 : biometrics
            # 66 - 74 : for future biometrics
            # 75 - 99 : for future data
            # 99 : local_id
        }

        return claim169


class MOSIPResponseError(BaseModel):
    """Errors encounted during MOSIP authentication process.

    Args:
        error_code (str): Type of error
        error_message (str): Description of error
        action_message (str): Suggested action to resolve error
    """
    error_code : str = Field(validation_alias="errorCode")
    error_message : str = Field(validation_alias="errorMessage")
    action_message : Optional[str] = Field(
            default=None,
            validation_alias="actionMessage"
        )

    def __str__(self) -> str :
        if self.action_message:
            return f"{self.error_code}: {self.error_message} ({self.action_message})"
        else:
            return f"{self.error_code}: {self.error_message}"


class MOSIPBaseResponseStatus(BaseModel):
    status : bool = Field(
        validation_alias=AliasChoices(
            "kycStatus", "authStatus"
        )
    )
    auth_token : Optional[str] = Field(
            default=None,
            validation_alias="authToken"
        )
    thumbprint : Optional[str] = Field(default=None)
    identity : Optional[str] = Field(default=None)
    session_key : Optional[str] = Field(
            default=None,
            validation_alias="sessionKey"
        )


class MOSIPOTPResponse(BaseModel):
    masked_mobile : Optional[str] = Field(
        default=None,
        validation_alias="maskedMobile"
        )
    masked_Email : Optional[str] = Field(
        default=None,
        validation_alias="maskedEmail"
        )


class MOSIPBaseResponse(BaseModel):
    """Base response model for MOSIP authentications.

    Attributes:
        transaction_id (str): MOSIP transaction id
        version (str): MOSIP Version
        id (str): id
        errors (ExceptionGroup): Errors during MOSIP authentication
        response_time (str): Transaction response time
        response (MOSIPResponseStatus): Result of response

    Raises:
        ExceptionGroup: Errors was encountered during the verification process
    """
    transaction_id : Optional[str] = Field(validation_alias="transactionID")
    version : Optional[str]
    id : Optional[str]
    errors : Optional[List[MOSIPResponseError]]
    response_time : str = Field(validation_alias="responseTime")
    response : Optional[MOSIPBaseResponseStatus]

    @property
    def status(self) -> bool :
        try:
            return self.response.status
        except NameError:
            return False

    @classmethod
    def from_response(cls, raw_response : Response ) -> Self :
        response_json = raw_response.json()
        return cls.model_validate(response_json)


class MOSIPKYCResponse(MOSIPBaseResponse):
    user : Optional[MOSIPUser] = Field(default=None)
    
    @classmethod
    def from_otp(cls, uid : str, txn_id : str, otp : str) -> Self :
        """Performs KYC verification using OTP.

        Args:
            uid (str): Unique identifier
            txn_id (str): transaction ID of KYC verification
            otp (str): OTP value
        """
        # OTP is 111111
        authenticator = manager.get_authenticator()

        raw_response = authenticator.kyc(
            individual_id=uid,
            individual_id_type="UIN",
            txn_id=txn_id,
            otp_value=otp,
            consent=True
        )

        return cls.from_response(raw_response)

    @classmethod
    def from_demographics(cls, uid : str, **data) -> Self :
        """Performs KYC verification using demographic data.

        Args:
            uid (str): User's UID
        """
        authenticator = manager.get_authenticator()
        demographic_data = _to_demographic_data(**data)

        raw_response = authenticator.kyc(
            individual_id=uid,
            individual_id_type="UIN",
            demographic_data=demographic_data,
            consent=True
        )

        kyc_response = cls.from_response(raw_response)

        if kyc_response.status:
            kyc_response.user = MOSIPUser.from_response(raw_response)
        
        return kyc_response


class MOSIPAuthResponse(MOSIPBaseResponse):
    @classmethod
    def from_otp(cls, uid : str, txn_id : str, otp : str) -> Self :
        """Performs user authentication using OTP.

        Args:
            uid (str): Unique identifier
            txn_id (str): transaction ID of KYC verification
            otp (str): OTP value
        """
        # OTP is 111111
        authenticator = manager.get_authenticator()

        raw_response = authenticator.auth(
            individual_id=uid,
            individual_id_type="UIN",
            txn_id=txn_id,
            otp_value=otp,
            consent=True
        )

        return cls.from_response(raw_response)

    @classmethod
    def from_demographics(cls, uid : str, **data) -> Self :
        """Performs user authentication using demographic data.

        Args:
            uid (str): Unique identifier
        """
        authenticator = manager.get_authenticator()
        demographic_data = _to_demographic_data(**data)

        raw_response = authenticator.auth(
            individual_id=uid,
            individual_id_type="UIN",
            demographic_data=demographic_data,
            consent=True
        )

        return cls.from_response(raw_response)


class MOSIPGenOTPResponse(MOSIPBaseResponse):
    response : Optional[MOSIPOTPResponse]

    @classmethod
    def start_otp(
        cls, 
        uid : str,
        use_email : bool = False,
        use_phone : bool = False
    ) -> Self : 
        authenticator = manager.get_authenticator()

        if not any([use_email, use_phone]):
            raise MOSIPMissingFieldError("Atleast one OTP method should be specified.")

        raw_response = authenticator.genotp(
            individual_id=uid,
            individual_id_type="UIN",
            email=use_email,
            phone=use_phone,
        )

        return cls.from_response(raw_response)

#TODO: Change exceptions to MOSIP model errors
#TODO: Find a way to enforce kyc gen OTP is used for kyc gen OTP
