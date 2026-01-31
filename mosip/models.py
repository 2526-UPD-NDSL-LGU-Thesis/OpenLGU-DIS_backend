"""
Models for MOSIP Collab user
"""

from datetime import datetime
from typing import Self, Dict

from mosip_auth_sdk import MOSIPAuthenticator
from mosip_auth_sdk.models import DemographicsModel
from app.settings import CONFIG


# pylint: disable=trailing-whitespace


# Initialize Authenticator.
authenticator = MOSIPAuthenticator(config=CONFIG)


class MOSIPException(Exception):
    '''MOSIP-related errors.'''


class MOSIPParserError(MOSIPException):
    '''`to_demographic_data` parsing errors during authentication.'''


# TODO Support other Demographic Parameters
def to_demographic_data(**kwargs : Dict[str, str | int | datetime]) -> DemographicsModel :
    '''
    A helper function that converts demographic data to `DemographicsModel` \
    for MOSIP Authentication.
    '''
    if not kwargs:
        raise ValueError("A demographpic field is required for authentication")

    data = {}

    for key, value in kwargs.items():
        match key:
            case "name" | "name_eng" :
                data["name"] = [{ "language": "eng", "value": value }]
            case "dob" :
                # Check if value is a valid date.
                if isinstance(value, str):
                    try:
                        datetime.strptime(value, r"%Y-%m-%d")
                        data["dob"] = value
                        continue
                    except ValueError as exc:
                        raise MOSIPParserError(
                            f"Unsupported date format: {value} must be in YYYY-MM-DD format."
                        ) from exc

                if isinstance(value, datetime):
                    data["dob"] = value.strftime(r"%Y-%m-%d")
                    
                raise MOSIPParserError(
                    f"Unsupported date value: {value} must be in YYYY-MM-DD format."
                )
            case _:
                raise MOSIPParserError(f"Unsupported parameter: {key}: {value}")
            
    return DemographicsModel(**data)


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
        User's face image in bytes form.
    
    
    For more information regarding the SDK, read the \
    [documentation](https://docs.mosip.io/1.2.0/id-lifecycle-management/identity-verification/id-authentication-services/mosip-authentication-sdk).
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

        self.response_body : dict

    @classmethod
    def verify(cls, id_ : int, **data) -> Self :
        """Verifies if given details is a MOSIP Collab user."""
        response_body = authenticator.kyc(
            individual_id=id_,
            individual_id_type="UIN",                       # Fixed id_type for now
            demographic_data=to_demographic_data(**data),
            consent=True
        ).json()

        if response_body["errors"]:
            exceptions = [
                Exception(f"{error['errorMessage']}: {error['actionMessage']}")
                for error in response_body["errors"]
            ]

            raise ExceptionGroup("Error encountered during MOSIP ID Verification.",
                exceptions
            )
        mosip_user = cls()
        mosip_user.uid = id_

        _decrypted_response = authenticator.decrypt_response(response_body=response_body)
        mosip_user.response_body = _decrypted_response

        for key, value in _decrypted_response.items():
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
                setattr(mosip_user, key, value)
        return mosip_user
