"""
https://medium.com/@ramanbazhanau/mastering-sqlalchemy-a-comprehensive-guide-for-python-developers-ddb3d9f2e829
"""

from typing import Self

from django.apps import AppConfig
from django.db import models
from django.conf import settings

from mosip_auth_sdk import MOSIPAuthenticator
from mosip_auth_sdk.models import DemographicsModel
from dynaconf import Dynaconf
from datetime import datetime
import os, json, qrcode

__all__ = (
    # "IDAuthenticator",
    "MOSIPCollabUser",
    "CompSciLabID",

    # "to_demographic_data",
)

os.path.isfile(r"./identity/certs/config.toml")

config = Dynaconf(settings_files=["./identity/certs/config.toml"], environments=False)
authenticator = MOSIPAuthenticator(config=config)

# TODO Support other Demographic Parameters
def to_demographic_data(name : str, dob : str) -> DemographicsModel:
    '''Converts passed parameters to type `DemographicsModel`.'''
    if not name and dob:
        raise ValueError("At least one of 'name' or 'dob' must be provided.")

    data = {}

    if name:
        data["name"] = [{ "language": "eng", "value": name }]
    if dob:
        data["dob"] = dob
    return DemographicsModel(**data)

# def IDAuthenticator(
#         id : str,
#         demographic_data : DemographicsModel,
#         id_type : str = "UIN",
#     ) -> dict :
    
    # response_body = authenticator.kyc(
    #     individual_id=id,
    #     individual_id_type=id_type,
    #     demographic_data=demographic_data,
    #     consent=True
    # ).json()

    # if response_body["errors"] == None:

    #     decrypted_response = authenticator.decrypt_response(response_body=response_body)

    #     return decrypted_response
    # else:
    #     return response_body["errors"][0]

from dataclasses import dataclass
from typing import Protocol

@dataclass
class IdentificationType(Protocol):
    # uid         : str
    # first_name  : str
    # middle_name : str
    # last_name   : str
    # suffix_name : str
    # sex         : str
    # gender      : str

    # @property
    # def middle_initial(self) -> str :
    #     """Returns the user's middle name initial/s."""
    #     return " ".join([
    #         f"{mn}." for mn in self.middle_name.split(" ")
    #     ]).title()
    
    # @property
    # def fullname(self) -> str :
    #     """Returns the user's full name."""
    #     return f"{self.first_name} {self.middle_initial} {self.last_name}".title()

    pass


class MOSIPCollabUser(IdentificationType):
    """User class that handles the response body of MOSIP Authentication SDK's KYC Auth. \

    
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
                Exception(f"{e['errorMessage']}: {e['actionMessage']}")
                for e in response_body["errors"]
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


class CompSciLabs(models.Model):
    """Class for Laboratories under the CS Department."""
    abbr    = models.CharField(primary_key=True, max_length=10)
    name    = models.CharField(max_length=70)


class CompSciDeptID(models.Model):
    """Class for IDs in the CS Department."""
    id          = models.BigIntegerField(primary_key=True, editable=True)
    name        = models.CharField(max_length=200, null=False)
    gender      = models.CharField(max_length=50, null=False)           #TODO Create choices for this
    dob         = models.DateField(null=False)
    location1   = models.CharField(max_length=200, null=False)
    phone       = models.CharField(max_length=11, null=True, blank=True)
    email       = models.EmailField(null=True, blank=True)
    face        = models.BinaryField(null=True, blank=True)
    

class CompSciLabID(models.Model):
    """Class for IDs in Laboratories under the CS Department."""
    id          = models.BigAutoField(primary_key=True)
    cslab       = models.ForeignKey(CompSciLabs, on_delete=models.CASCADE)
    csdept      = models.ForeignKey(CompSciDeptID, on_delete=models.CASCADE)
    issued_at   = models.DateField(auto_now_add=True)
    file        = models.FileField(upload_to="uploads/")
    verified    = models.BooleanField(default=False)

# from PIL import Image, ImageDraw, ImageFont

# # from .models import MOSIPCollabUser

# # Templates
# NDSG_TEMPLATE = r'./static/img/labs/ndsg-template.png'

# FONT_PATH= r'./static/fonts/Roboto/static/Roboto-Regular.ttf'

# def generate_id(id_: MOSIPCollabUser) -> None :
#     '''
#     Docstring for generate_id
    
#     :param id: Description
#     :type id: MOSIPCollabUser
#     :param id_number: Description
#     :return: Description
#     :rtype: Any
#     '''
#     # Load the ID template image
#     id_image = Image.open(NDSG_TEMPLATE)

#     # Initialize drawing context
#     draw = ImageDraw.Draw(id_image)

#     # Load the Roboto font
#     font = ImageFont.truetype(FONT_PATH, 40)

#     # Position of text and fields
#     photo_x, photo_y =  62, 78                  # Coordinates for the photo position (top-left corner)
#     photo_width, photo_height = 300, 400        # Photo size (width x height)

#     # Add the fields on the ID template
#     line_height = 50  # Line height for spacing between fields
#     x_offset = 40  # Horizontal offset for text
#     y_offset = photo_y  # Starting position for the fields below the photo

#     fields = {
#         "Name": id_.name,
#         "Gender": id_.gender,
#         "DOB": id_.dob,
#         "Address": id_.location1,
#         "Email": id_.email,
#         "ID No": id_.uid
#     }
    
#     # Add each field text dynamically
#     for label, value in fields.items():
#         # Draw the label and value on the image
#         draw.text((photo_x + photo_width + x_offset, y_offset), f"{label}: {value}", fill="black", font=font)
#         y_offset += line_height  # Move to the next line

#     # Save the updated image
#     id_image.save(fr"static/img/ids/ID{id_.uid}.png")