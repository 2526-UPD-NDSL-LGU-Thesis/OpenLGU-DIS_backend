"""
https://medium.com/@ramanbazhanau/mastering-sqlalchemy-a-comprehensive-guide-for-python-developers-ddb3d9f2e829
"""

from django.db import models


class User:
    firstName   = ...
    middleName  = ...
    lastName    = ...
    suffixName  = ...

    def fullname(self) -> str :
        """Returns the User's full name."""
        _full_name = f"{self.firstName} {self.middleName} {self.lastName}"
        
        if self.suffixName:
            _full_name += f", {self.suffixName}"

        return _full_name

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