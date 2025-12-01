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

from .models import CompSciLabID, CompSciDeptID, CompSciLabs
from .serializers import CompSciLabIDSerializer, CompSciDeptIDSerializer, CompSciLabsSerializer

__all__ = (
    'profile',
    'register',
    'CompSciLabIDViewSet',
    'CompSciDeptIDViewSet',
    'CompSciLabsViewSet',
)

def profile(request) -> HttpResponse :
    '''Render profile page.'''
    return render(request, "profile.html")

def register(request) -> HttpResponse :
    '''Render register page.'''
    return render(request, "register.html")

@authentication_classes([BasicAuthentication])
class CompSciLabIDViewSet(viewsets.ModelViewSet):
    '''View set for `CompSciLabID`.'''
    http_method_names = ['get', 'post']
    permission_classes = [AllowAny]
    queryset = CompSciLabID.objects.all()
    serializer_class = CompSciLabIDSerializer

    @action(detail=True, methods=['GET'], url_path='qr')
    def qr(self, request, pk=None):
        lab_id = self.get_object()

        qr_data = {
            "cs_dept_id" : lab_id.csdept.id,
            "cs_lab"     : lab_id.cslab.abbr,
            "cs_lab_id"  : lab_id.id,
            "issued_at"  : lab_id.issued_at.strftime("%Y-%m-%d")
        }

        print(qr_data)

        json_string = json.dumps(qr_data)

        qr = qrcode.make(json_string)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        # return HttpResponse(buffer, content_type="image/png")

        qr.show()
    
    @action(detail=True, methods=['GET'], url_path='id')
    def id(self, request, pk=None):
        lab_id = self.get_object()
        dept_id = lab_id.csdept

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
            "Name": dept_id.name,
            "Gender": dept_id.gender,
            "DOB": dept_id.dob,
            "Address": dept_id.location1,
            "Email": dept_id.email,
            "ID No": dept_id.id
        }
        
        # Add each field text dynamically
        for label, value in fields.items():
            # Draw the label and value on the image
            draw.text((photo_x + photo_width + x_offset, y_offset), f"{label}: {value}", fill="black", font=font)
            y_offset += line_height  # Move to the next line

        # Save the updated image
        id_image.show()


@authentication_classes([BasicAuthentication])
class CompSciDeptIDViewSet(viewsets.ModelViewSet):
    '''View set for `CompSciDeptID`.'''
    http_method_names = ['get', 'post']
    permission_classes = [AllowAny]
    queryset = CompSciDeptID.objects.all()
    serializer_class = CompSciDeptIDSerializer


@authentication_classes([BasicAuthentication])
class CompSciLabsViewSet(viewsets.ModelViewSet):
    '''View set for `CompSciLabs`.'''
    http_method_names = ['get']
    permission_classes = [AllowAny]
    queryset = CompSciLabs.objects.all()
    serializer_class = CompSciLabsSerializer