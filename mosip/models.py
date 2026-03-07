"""
Models for MOSIP Collab user
"""

import base64
from datetime import datetime
from typing import Self, Dict, List

from dynaconf import Dynaconf
from mosip_auth_sdk import MOSIPAuthenticator
from mosip_auth_sdk.models import DemographicsModel
from requests.models import Response
import numpy as np
import cv2



# pylint: disable=trailing-whitespace


# Initialize Authenticator.
config = Dynaconf(settings_files=["./config.toml"], environments=False)
authenticator = MOSIPAuthenticator(config=config)


class MOSIPException(Exception):
    '''MOSIP-related errors.'''


class MOSIPParserError(MOSIPException):
    '''`to_demographic_data` parsing errors during authentication.'''


# TODO Support other Demographic Parameters
# TODO Support other languages
# Do we support other languages?
def to_demographic_data(**kwargs) -> DemographicsModel :
    '''
    A helper function that converts demographic data to `DemographicsModel` \
    for MOSIP Authentication.
    '''
    def to_identity_info(value : str, language : str = "eng") -> List[Dict[str, str]] :
        '''A helper function that converts value to `IdentityInfo`.'''
        return [{ "language": language, "value": value }]
    
    # How many KYC points are we going to implement?
    if not kwargs:
        raise ValueError("A demographpic field is required for authentication")

    data = {}

    for key, value in kwargs.items():
        match key:
            # Check if age is a valid integer.
            case "age" :
                try:
                    data["age"] = str(int(value))
                except ValueError as exc:
                    raise MOSIPParserError(
                        f"Invalid data type: Age should be an integer, not {type(value)}."
                    ) from exc
            
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
                    except Exception as exc:
                        raise MOSIPParserError(
                            f"Unsupported date format: {value} must be in %Y/%m/%d format."
                        ) from exc
                    finally:
                        continue

                if isinstance(value, datetime):
                    data["dob"] = value.strftime(r"%Y/%m/%d")
                    continue
                
                raise MOSIPParserError(
                    f"Unsupported date value: {value} must be in %Y/%m/%d format."
                )
            
            # If no language is set, name is accepted as English.
            # TODO create config file for default language code (?)
            # TODO catch error of invalid language code
            case _ if key.startswith("name") :
                try:
                    _, language = key.strip("_")
                    data["name"] = to_identity_info(value, language=language)
                # except
                except ValueError:
                    data["name"] = to_identity_info(value)

            case _ if key.startswith("dob_type") :
                try:
                    _, _, language = key.strip("_")
                    data["dob_type"] = to_identity_info(value, language=language)
                # except
                except ValueError:
                    data["dob_type"] = to_identity_info(value)

            case _ if key.startswith("gender") :
                try:
                    _, language = key.strip("_")
                    data["gender"] = to_identity_info(value, language=language)
                # except
                except ValueError:
                    data["gender"] = to_identity_info(value)
            
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
                        f"Invalid Phone Number: {value} is invalid or not supported."
                    )
            
                data["phone_number"] = value


            # TODO Email verification
            case "email_id" :
                data["email_id"] = value.lower()

            case _ if key.startswith("addressLine1") :
                try:
                    _, _, language = key.strip("_")
                    data["address_line1"] = to_identity_info(value, language=language)
                # except
                except ValueError :
                    data["address_line1"] = to_identity_info(value)
            
            case _ if key.startswith("addressLine2") :
                try:
                    _, _, language = key.strip("_")
                    data["address_line2"] = to_identity_info(value, language=language)
                # except
                except ValueError :
                    data["address_line2"] = to_identity_info(value)

            case _ if key.startswith("addressLine3") :
                try:
                    _, _, language = key.strip("_")
                    data["address_line3"] = to_identity_info(value, language=language)
                # except
                except ValueError :
                    data["address_line3"] = to_identity_info(value)

            case _ if key.startswith("location1") :
                try:
                    _, language = key.strip("_")
                    data["location1"] = to_identity_info(value, language=language)
                # except
                except ValueError :
                    data["location1"] = to_identity_info(value)

            case _ if key.startswith("location2") :
                try:
                    _, language = key.strip("_")
                    data["location2"] = to_identity_info(value, language=language)
                # except
                except ValueError :
                    data["location2"] = to_identity_info(value)

            case _ if key.startswith("location3") :
                try:
                    _, language = key.strip("_")
                    data["location3"] = to_identity_info(value, language=language)
                # except
                except ValueError :
                    data["location3"] = to_identity_info(value)

            case "postal_code" :
                if value.isdigit() and len(value) == 4:
                    data["postal_code"] = value
                else:
                    raise MOSIPParserError(
                        f"Invalid Postal Code: {value} must be a 4-digit code."
                    )

            case _ if key.startswith("full_address") :
                try:
                    _, _, language = key.strip("_")
                    data["full_address"] = to_identity_info(value, language=language)
                # except
                except ValueError :
                    data["full_address"] = to_identity_info(value)

            case _ :
                raise MOSIPParserError(f"Unsupported parameter: {key}: {value}")
            
    return DemographicsModel(**data)


def decode_face(face_b64 : str) -> str :
    """Decode face data from MOSIP response body to base64 string."""
    face_bytes = base64.b64decode(face_b64)
    face_as_np = np.frombuffer(face_bytes[73:], dtype=np.uint8)
    img = cv2.imdecode(face_as_np, cv2.IMREAD_COLOR)
    _, buffer = cv2.imencode(".jpg", img)
    return base64.b64encode(buffer).decode("utf-8")


def start_otp(pcn : int, email_otp : bool = False, phone_otp : bool = False) -> str :
    """Starts the OTP Authentication process for `verify_otp`."""
    response = authenticator.genotp(
        individual_id=pcn,
        individual_id_type="UIN",
        email=email_otp,
        phone=phone_otp
    )
    response_body = response.json()

    return response_body["transactionID"]


class MOSIPCollabUser:
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
    def __init__(self) -> None :
        self.uid        : int
        self.name       : dict[str, str] = {}
        self.gender     : dict[str, str] = {}
        self.dob        : str
        self.location1  : dict[str, str] = {}
        self.phone      : str
        self.email      : str
        self.face       : bytes

    @classmethod
    def _decode(cls, response : Response) -> Self :
        """Decodes the MOSIP response body."""
        response_body = response.json()

        if response_body["errors"]:
            exceptions = [
                # Exception(f"{error['errorMessage']}: {error['actionMessage']}")
                Exception(f"{error['errorMessage']}")
                for error in response_body["errors"]
            ]

            raise ExceptionGroup("Error encountered during MOSIP Authentication.",
                exceptions
            )
        
        mosip_user = cls()

        decrypted_response = authenticator.decrypt_response(response_body)

        for key, value in decrypted_response.items():
            try:
                key_var, key_lang = key.split("_")

                match key_var:
                    case "name":
                        mosip_user.name[key_lang] = value
                    case "gender":
                        mosip_user.gender[key_lang] = value
                    case "location1":
                        mosip_user.location1[key_lang] = value
                    case _:
                        raise Warning(f"Unsupported parameter: {key_var}.")
            except ValueError:
                if key == "face":
                    image_b64 = decode_face(decrypted_response["face"])

                    setattr(mosip_user, key, image_b64)
                else:
                    setattr(mosip_user, key, value)
        return mosip_user

    @classmethod
    def verify_kyc(cls, pcn : int, **data) -> Self :
        """Verifies if given details is a MOSIP Collab user using the KYC Authentication."""
        # TODO Investigate different types of `individual_id_type`
        response = authenticator.kyc(
            individual_id=pcn,
            individual_id_type="UIN",
            demographic_data=to_demographic_data(**data),
            consent=True
        )
        
        return cls._decode(response)
    
    @classmethod
    def verify_otp(cls, pcn : int, txn_id : str, otp : str) -> Self :
        """Verifies if given details is a MOSIP Collab user using the OTP Authentication."""
        # OTP is 111111
        response = authenticator.kyc(
            individual_id=pcn,
            individual_id_type="UIN",
            txn_id=txn_id,
            otp_value=otp,
            consent=True
        )

        return cls._decode(response)

    @property
    def info(self) -> Dict[str, str | int] :
        '''
        User's demographic information without the face data.
        '''

        return {
            key: value for key, value in self.__dict__.items()
            if key != "face"
        }
