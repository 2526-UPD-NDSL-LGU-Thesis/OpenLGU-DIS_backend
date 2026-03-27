"""
Pydantic Models for MOSIP Collab user
"""

import base64
from datetime import datetime
from dataclasses import dataclass
from io import BytesIO
from typing import Self, Dict, List, Any, Optional, Union

from django.conf import settings
from dynaconf import Dynaconf
from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue
from mosip_auth_sdk import MOSIPAuthenticator
from mosip_auth_sdk.models import DemographicsModel
from pydantic import BaseModel, Field
from PIL import Image
from requests.models import Response

# pylint: disable=trailing-whitespace
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name

# Initialize Authenticator.
config = Dynaconf(settings_files=["./mosip/mosip_config.toml"], environments=False)
authenticator = MOSIPAuthenticator(config=config)


class MOSIPException(Exception):
    """MOSIP-related errors."""


class MOSIPParserError(MOSIPException):
    """Data cleaning and parsing errors during `to_demographic_data`."""


class MOSIPResponseError(BaseModel):
    """Errors encounted during MOSIP authentication process."""
    errorCode       : str
    errorMessage    : str
    actionMessage   : str

    @classmethod
    def from_dict(cls, error : Dict[str, str]) -> Self :
        return cls(**error)

    def __str__(self) -> str :
        return f"{self.errorCode}: {self.errorMessage} ({self.actionMessage})"


class MOSIPAuthStatus(BaseModel):
    authStatus  : bool
    authToken   : str

    @classmethod
    def from_response(cls, response : Response) -> Self :
        response = response.json()
        return cls(**response)


def _to_demographic_data(**kwargs) -> DemographicsModel :
    """A helper function that converts demographic data to a `DemographicsModel` \
    for MOSIP Authentication.

    :param kwargs: Demographic keyword arguments:\n
        - Name
    """

    def _to_identity_info(
            value : str,
            language : str = settings.DEFAULT_LANGUAGE_ISO
        ) -> List[Dict[str, str]] :
        """A helper function that converts value to `IdentityInfo`."""
        return [{ "language": language, "value": value }]
    
    # TODO: How many KYC points are we going to implement?
    if not kwargs:
        raise ValueError("A demographpic field is required for authentication")

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
                    raise MOSIPParserError(
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
                        raise MOSIPParserError(
                            f"Unsupported date format: {value} must be in %Y/%m/%d format"
                        ) from err
                    finally:
                        continue

                if isinstance(value, datetime):
                    data["dob"] = value.strftime(r"%Y/%m/%d")
                    continue
                
                raise MOSIPParserError(
                    f"Unsupported date value: {value} must be in %Y/%m/%d format"
                )
            

            case _ if key.startswith("name") :
                try:
                    _, language = key.split("_")
                    Lang(pt3=language)
                    data["name"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPException(
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
                    raise MOSIPException(
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
                    raise MOSIPException(
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
                    raise MOSIPParserError(
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
                    raise MOSIPException(
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
                    raise MOSIPException(
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
                    raise MOSIPException(
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
                    raise MOSIPException(
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
                    raise MOSIPException(
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
                    raise MOSIPException(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["location3"] = _to_identity_info(value)

            case "postal_code" :
                if value.isdigit() and len(value) == 4:
                    data["postal_code"] = value
                else:
                    raise MOSIPParserError(
                        f"Invalid Postal Code: {value} must be a 4-digit code"
                    )

            case _ if key.startswith("full_address") :
                try:
                    _, _, language = key.split("_")
                    Lang(pt3=language)
                    data["full_address"] = _to_identity_info(value, language=language)
                except InvalidLanguageValue as err:
                    raise MOSIPException(
                        f"{language} from {key} is not a valid ISO639-3 language code"
                    ) from err
                except ValueError :
                    data["full_address"] = _to_identity_info(value)

            case _ :
                raise MOSIPParserError(f"Unsupported parameter: {key}: {value}")
            
    return DemographicsModel(**data)


def decode_face(face_b64 : str) -> str :
    """Decode face image bytes from MOSIP response body to base64 string."""
    face_bytes = base64.b64decode(face_b64)[73:]
    face_img = Image.open(BytesIO(face_bytes[:73]))
    try:
        face_img.load()
    except Exception as err:
        raise MOSIPException("Failed to decode image") from err

    return base64.b64encode(face_bytes).decode("utf-8")


def start_otp(uid : int, email_otp : bool = False, phone_otp : bool = False) -> str :
    """Starts the OTP Authentication process for `verify_otp`."""
    response = authenticator.genotp(
        individual_id=uid,
        individual_id_type="UIN",
        email=email_otp,
        phone=phone_otp
    )
    response_body = response.json()

    return response_body["transactionID"]


@dataclass
class MOSIPUser(BaseModel):
    """
    User class that handles the response body of MOSIP Authentication SDK's KYC Auth. \

    
    Interfaces the decrypted response body of a successful authentication transaction. \
    Otherwise, raise an `ExceptionGroup` of all errors from response body when authentication \
    fails.

    
    Attributes
    ----------
    name        : dict[str, str]
        A dictionary of the user's name in different locales.
    gender      : dict[str, str]
        A dictionary of the user's gender in different locales.
    dob         : str
        User's date of birth.
    location1   : dict[str, str]
        A dictionary of the user's location in different locales.
    phone       : str
        User's phone number.
    email       : str
        User's email address.
    face        : bytes
        User's face image in base64 bytes form.
    
    
    For more information regarding the SDK, read the \
    [documentation](https://docs.mosip.io/1.2.0/id-lifecycle-management/identity-verification/id-authentication-services/mosip-authentication-sdk).     # pylint: disable=line-too-long
    """
    uid        : int
    name       : Dict[str, str] = Field(default_factory=dict)
    gender     : Dict[str, str] = Field(default_factory=dict)
    dob        : str
    location1  : Dict[str, str] = Field(default_factory=dict)
    phone      : str
    email      : str
    face       : bytes

    @classmethod
    def from_response(cls, response : Response) -> Self :
        """Decrypt the MOSIP response body."""
        response = response.json()

        mosip_user = {}

        decrypted_response = authenticator.decrypt_response(response)

        for key, value in decrypted_response.items():
            try:
                key_var, key_lang = key.split("_")

                match key_var:
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

    @classmethod
    def kyc_via_demographics(cls, uid : int, **data) -> Self :
        """Verifies if given details is a MOSIP Collab user using the KYC Authentication.

        :param uid: User's MOSIP ID.
        :type uid: int
        :return: Returns a `MOSIPCollabUser` or an `ExceptionGroup`.
        :rtype: Self
        """
        response = authenticator.kyc(
            individual_id=uid,
            individual_id_type="UIN",
            demographic_data=_to_demographic_data(**data),
            consent=True
        )
        
        return cls.from_response(response)

    @classmethod
    def auth_via_demographics(cls, uid : int, **data) -> Self :
        """Verifies if given details is a MOSIP Collab user using the KYC Authentication.

        :param uid: User's MOSIP ID.
        :type uid: int
        :return: Returns a `MOSIPCollabUser` or an `ExceptionGroup`.
        :rtype: Self
        """
        response = authenticator.auth(
            individual_id=uid,
            individual_id_type="UIN",
            demographic_data=_to_demographic_data(**data),
            consent=True
        )

        return cls.from_response(response)
    
    @classmethod
    def kyc_via_otp(cls, uid : int, txn_id : str, otp : str) -> Self :
        """Verifies if given details is a MOSIP Collab user using the OTP Authentication."""
        # OTP is 111111
        response = authenticator.kyc(
            individual_id=uid,
            individual_id_type="UIN",
            txn_id=txn_id,
            otp_value=otp,
            consent=True
        )

        return cls.from_response(response)

    @property
    def info(self) -> Dict[str, str | int] :
        """
        User's demographic information without the face data.
        """

        return {
            key: value for key, value in self.__dict__.items()
            if key != "face"
        }


class MOSIPResponse(BaseModel):
    transactionID   : str
    version         : str
    id              : str
    errors          : Optional[List[MOSIPResponseError]]
    responseTime    : str
    response        : Optional[Union[MOSIPUser, MOSIPAuthStatus]]

    @classmethod
    def from_response(cls, response : Response) -> Self :
        response_json = response.json()
        response_body_errors = response_json["errors"]

        if response_body_errors:
            errors = [
                MOSIPResponseError(**err)
                for err in response_body_errors
            ]
        else:
            errors = []
        
        try:
            response = MOSIPUser.from_response(response)
        except:
            response = MOSIPAuthStatus.from_response(response)

        return cls(
            transactionID=response_json["transactionID"],
            version=response_json["version"],
            id=response_json["id"],
            errors=errors,
            responseTime=response_json["responseTime"],
            response=response,
        )
