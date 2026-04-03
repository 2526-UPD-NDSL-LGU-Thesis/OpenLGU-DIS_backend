import base64
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from typing import Self, Dict, List, Optional, Union

from django.conf import settings
from dynaconf import Dynaconf
from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue
from mosip_auth_sdk import MOSIPAuthenticator
from mosip_auth_sdk.models import DemographicsModel
from pydantic import BaseModel, Field, AliasChoices, computed_field, field_validator
from PIL import Image
from requests.models import Response


def decode_face(face_b64 : str) -> str :
    """Decode face image bytes from MOSIP response body to Base64 string."""
    face_bytes = base64.b64decode(face_b64)[73:]
    face_img = Image.open(BytesIO(face_bytes))
    try:
        face_img.load()
    except Exception as err:
        raise MOSIPException("Failed to decode image") from err

    return base64.b64encode(face_bytes).decode("utf-8")


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


def get_authenticator():
    pass


def _to_demographic_data(**kwargs) -> DemographicsModel :
    """A helper function that converts demographic data to a `DemographicsModel` \
    for MOSIP Authentication.

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
    
    Returns:
        DemographicsModel: A populated `DemographicsModel` instance ready for MOSIP Authentication.
    """

    def _to_identity_info(
            value : str,
            # language : str = settings.DEFAULT_LANGUAGE_ISO
            language : str = "eng"
        ) -> List[Dict[str, str]] :
        """A helper function that converts value to `IdentityInfo`."""
        return [{ "language": language, "value": value }]
    
    if not kwargs:
        raise MOSIPMissingFieldError("A demographpic field is required for authentication")

    data = {}

    for key, value in kwargs.items():
        language = None
        key = key.lower()
        
        match key:
            # Check if age is a valid integer.
            case "age" :
                try:
                    data["age"] = str(int(value))
                except ValueError as err:
                    raise MOSIPParsingError(
                        f"Invalid data type: Age should be an integer, not {type(value)}"
                    ) from err
            
            # Check if dob is a valid date and follows the correct format %Y/%m/%d.
            # If it does not follow the same format, (e.g. using "-" instead of "/"),
            # correct it so that authentication does not fail.
            # `DemographicsModel` will accept this but this will raise an error during
            # authentication.
            case "dob" :
                if isinstance(value, str):
                    try:
                        datetime.strptime(value, r"%Y/%m/%d")
                        data["dob"] = value
                    except ValueError:
                        datetime.strptime(value, r"%Y-%m-%d")
                        data["dob"] = value.replace("-", "/")
                    except Exception as err:
                        raise MOSIPParsingError(
                            f"Unsupported date format: {value} must be in %Y/%m/%d format"
                        ) from err
                    finally:
                        continue

                if isinstance(value, datetime):
                    data["dob"] = value.strftime(r"%Y/%m/%d")
                    continue
                
                raise MOSIPParsingError(
                    f"Unsupported date value: {value} must be in %Y/%m/%d format"
                )

            case _ if key.startswith("name") :
                try:
                    _, language = key.split("_")
                    Lang(pt3=language)
                    data["name"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError:
                    data["name"] = _to_identity_info(value)
                finally:
                    continue

            case _ if key.startswith("dob_type") :
                try:
                    _, _, language = key.split("_")
                    Lang(pt3=language)
                    data["dob_type"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError:
                    data["dob_type"] = _to_identity_info(value)
                finally:
                    continue

            case _ if key.startswith("gender") :
                try:
                    _, language = key.split("_")
                    Lang(pt3=language)
                    data["gender"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError:
                    data["gender"] = _to_identity_info(value)
                finally:
                    continue
            
            # TODO Data validation for phone number
            case "phone_number" :
                # Check if number is type 09XX XXX XXXX
                if value.isdigit() and len(value) == 11:
                    # Check if valid SIM Carrier
                    pass
                
                # Check if number is type +63 9xx xxx xxxx
                elif value.startswith("+63") and len(value) == 13:
                    # Check if valid SIM Carrier
                    pass
                
                else:
                    raise MOSIPParsingError(
                        f"Invalid Phone Number: {value} is invalid or not supported"
                    )
            
                data["phone_number"] = value


            # TODO Email verification
            case "email_id" :
                data["email_id"] = value.lower()

            case _ if key.startswith("addressLine1") :
                try:
                    _, _, language = key.split("_")
                    Lang(pt3=language)
                    data["address_line1"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["address_line1"] = _to_identity_info(value)
            
            case _ if key.startswith("addressLine2") :
                try:
                    _, _, language = key.split("_")
                    Lang(pt3=language)
                    data["address_line2"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["address_line2"] = _to_identity_info(value)

            case _ if key.startswith("addressLine3") :
                try:
                    _, _, language = key.split("_")
                    Lang(pt3=language)
                    data["address_line3"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["address_line3"] = _to_identity_info(value)

            case _ if key.startswith("location1") :
                try:
                    _, language = key.split("_")
                    Lang(pt3=language)
                    data["location1"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["location1"] = _to_identity_info(value)

            case _ if key.startswith("location2") :
                try:
                    _, language = key.split("_")
                    Lang(pt3=language)
                    data["location2"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["location2"] = _to_identity_info(value)

            case _ if key.startswith("location3") :                
                try:
                    _, language = key.split("_")
                    Lang(pt3=language)
                    data["location3"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["location3"] = _to_identity_info(value)

            case "postal_code" :
                if value.isdigit() and len(value) == 4:
                    data["postal_code"] = value
                else:
                    raise MOSIPParsingError(
                        f"Invalid Postal Code: {value} must be a 4-digit code"
                    )

            case _ if key.startswith("full_address") :
                try:
                    _, _, language = key.split("_")
                    Lang(pt3=language)
                    data["full_address"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPLanguageError(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["full_address"] = _to_identity_info(value)

            case _ :
                raise MOSIPParsingError(f"Unsupported parameter: {key}: {value}")
            
    return DemographicsModel(**data)


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

    @classmethod
    def from_dict(cls, error : Dict[str, str]) -> Self :
        return cls(**error)

    def __str__(self) -> str :
        return f"{self.error_code}: {self.error_message} ({self.action_message})"


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


class MOSIPGenOTPResponse(BaseModel):
    masked_mobile : str = Field(validation_alias="maskedMobile")
    masked_Email : str = Field(validation_alias="maskedEmail")


class MOSIPUser(BaseModel):
    """User class from MOSIP Authentication SDK's response body.

    Interfaces the decrypted response body of a successful authentication transaction. \
    Otherwise, raise an `ExceptionGroup` of all errors from response body when authentication \
    fails.

    For more information regarding the SDK, see the documentation:
    https://docs.mosip.io/1.2.0/id-lifecycle-management/identity-verification/id-authentication-services/mosip-authentication-sdk
    
    Attributes:
        uid (int): User's unique identifier
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
    # uid        : int
    name       : Dict[str, str] = Field(default_factory=dict)
    gender     : Dict[str, str] = Field(default_factory=dict)
    dob        : str
    location1  : Dict[str, str] = Field(default_factory=dict)
    phone      : str
    email      : str
    face       : bytes

    @classmethod
    def from_response(cls, raw_response : Response) -> Self :
        """Decrypt User info from MOSIP response."""
        raw_response = raw_response.json()

        mosip_user = defaultdict(dict)

        decrypted_response = authenticator.decrypt_response(raw_response)

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
    def from_otp(cls, uid : int, txn_id : str, otp : str) -> Self :
        """Performs KYC verification using OTP.

        Args:
            uid (int): Unique identifier
            txn_id (str): transaction ID of KYC verification
            otp (str): OTP value
        """
        # OTP is 111111
        raw_response = authenticator.kyc(
            individual_id=uid,
            individual_id_type="UIN",
            txn_id=txn_id,
            otp_value=otp,
            consent=True
        )

        return cls.from_response(raw_response)

    @classmethod
    def from_demographics(cls, uid : int, **data) -> Self :
        """Performs KYC verification using demographic data.

        Args:
            uid (int): User's UID
        """
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
    def from_otp(cls, uid : int, txn_id : str, otp : str) -> Self :
        """Performs user authentication using OTP.

        Args:
            uid (int): Unique identifier
            txn_id (str): transaction ID of KYC verification
            otp (str): OTP value
        """
        # OTP is 111111
        raw_response = authenticator.auth(
            individual_id=uid,
            individual_id_type="UIN",
            txn_id=txn_id,
            otp_value=otp,
            consent=True
        )

        return cls.from_response(raw_response)

    @classmethod
    def from_demographics(cls, uid : int, **data) -> Self :
        """Performs user authentication using demographic data.

        Args:
            uid (int): Unique identifier
        """
        demographic_data = _to_demographic_data(**data)

        raw_response = authenticator.auth(
            individual_id=uid,
            individual_id_type="UIN",
            demographic_data=demographic_data,
            consent=True
        )

        return cls.from_response(raw_response)


config = Dynaconf(settings_files=["./mosip/mosip_config.toml"], environments=False)
authenticator = MOSIPAuthenticator(config=config)

# kyc auth
demographics_data = DemographicsModel(
    name=[{"language": "eng", "value": "James Rodrigious"}],
)

print()
response = authenticator.kyc(
    individual_id="2047631038",
    individual_id_type="UIN",
    demographic_data=demographics_data,
    consent=True,
)
decrypted_response = authenticator.decrypt_response(response.json())
print("response: ", decrypted_response.keys())
print()

# print("Response: ", response.json().keys())
# response = MOSIPBaseResponse.from_response(response)
# print("Response Model: ", response.model_dump().keys())
# print("Response Response Model: ", response.response.model_dump().keys())

# response = MOSIPKYCResponse.from_demographics(uid="2047631038", 
#     name="James Rodrigious"
# )
# print(response.model_dump().keys())
# print(response.user.model_dump().keys())
# print(response.errors)


# response = authenticator.auth(
#     individual_id="2047631038",
#     individual_id_type="UIN",
#     demographic_data=demographics_data,
#     consent=True,
# )
# response_body = response.json()
# print("auth via demographics", response_body.keys())
# print("response", response_body["response"].keys())
# print()

# response = authenticator.genotp(
#     individual_id="2047631038",
#     individual_id_type="UIN",
#     email=True,
#     phone=True,
# )
# print(type(response))
# response_body = response.json()
# transaction_id = response_body["transactionID"]
# response = authenticator.kyc(
#     individual_id="2047631038",
#     individual_id_type="UIN",
#     otp_value="111111",
#     consent=True,
#     txn_id=transaction_id,
# )
# response_body = response.json()
# print("kyc via otp", response_body.keys())
# decrypted_response = authenticator.decrypt_response(response_body)
# print("response: ", decrypted_response.keys())
# print()

# response = authenticator.genotp(
#     individual_id="2047631038",
#     individual_id_type="UIN",
#     email=True,
#     phone=True,
# )
# response_body = response.json()
# transaction_id = response_body["transactionID"]
# response = authenticator.auth(
#     individual_id="2047631038",
#     individual_id_type="UIN",
#     otp_value="111111",
#     consent=True,
#     txn_id=transaction_id,
# )
# response_body = response.json()
# print("auth via otp", response_body.keys())
# print("response", response_body["response"].keys())
# print()