'''
Django views for `identity` app.
'''

from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import authentication_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import viewsets
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import qrcode
import json

from .models import User
from .serializers import UserSerializer

__all__ = (
    'profile',
    'register',
    'UserViewSet',
)

def profile(request, lgu_id=None) -> HttpResponse :
    '''Render profile page.'''
    context = {}
    if lgu_id:
        context['lgu_id'] = lgu_id
    return render(request, "profile.html", context=context)

def register(request) -> HttpResponse :
    '''Render register page.'''
    return render(request, "register.html")

@authentication_classes([BasicAuthentication])
class UserViewSet(viewsets.ModelViewSet):
    '''View set for `User`.'''
    http_method_names = ['get', 'post']
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=['GET'], url_path='qr')
    def qr(self, request, pk=None):
        user_id = self.get_object()

        qr_data = {
            "user_id" : user_id.id,
            "issued_at"  : user_id.issued_at.strftime("%Y-%m-%d")
        }

        print(qr_data)

        json_string = json.dumps(qr_data)

        qr = qrcode.make(json_string)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        # qr.show()
        return HttpResponse(buffer, content_type="image/png")
    
    @action(detail=True, methods=['GET'], url_path='id')
    def id(self, request, pk=None):
        _id = self.get_object()

        # Load the ID template image
        id_image = Image.open(
            r'./identity/static/img/labs/ndsg-template.png'
        )

        # Initialize drawing context
        draw = ImageDraw.Draw(id_image)

        # Load the Roboto font
        font = ImageFont.truetype(
            r'./identity/static/fonts/Roboto/static/Roboto-Regular.ttf', 40
        )

        # Position of text and fields
        photo_x, photo_y =  62, 78                  # Coordinates for the photo position (top-left corner)
        photo_width, photo_height = 300, 400        # Photo size (width x height)

        # Add the fields on the ID template
        line_height = 50  # Line height for spacing between fields
        x_offset = 40  # Horizontal offset for text
        y_offset = photo_y  # Starting position for the fields below the photo

        fields = {
            # "Name": _id.name,
            # "Sex": _id.sex,
            "DOB": _id.birthdate,
            "ID": _id.id,
            "PCN": _id.pcn,
            "Verified": _id.verified
        }
        
        # Add each field text dynamically
        for label, value in fields.items():
            # Draw the label and value on the image
            draw.text((photo_x + photo_width + x_offset, y_offset), f"{label}: {value}", fill="black", font=font)
            y_offset += line_height  # Move to the next line

        # Save the updated image
        # id_image.show()
        buffer = BytesIO()
        id_image.save(buffer, format="PNG")
        buffer.seek(0)
        
        return HttpResponse(buffer, content_type="image/png")