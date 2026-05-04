'''
Django views for `identity` app.
'''

from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status

from .models import Resident, ResidentSector
from .serializers import UserGroupSerializer, UserSerializer, ResidentSerializer, SectorSerializer


def profile(request, lgu_id=None) -> HttpResponse :
    '''Render profile page.'''
    context = {}
    if lgu_id:
        context['lgu_id'] = lgu_id
    return render(request, "profile.html", context=context)

def register(request) -> HttpResponse :
    '''Render register page.'''
    return render(request, "register.html")

def claim(request) -> HttpResponse :
    '''Render claim page.'''
    return render(request, "claim.html")

def auth(request) -> HttpResponse :
    return render(request, "auth.html")


class UserGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = UserGroupSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ResidentViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    '''View set for `User`.'''
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    lookup_field = 'uin'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, uin=self.kwargs["uin"])
        self.check_object_permissions(self.request, obj)
        return obj
    
    @action(detail=False, methods=['GET'], url_path=r"pcn/(?P<pcn>[^/.]+)")
    def by_pcn(self, request, pcn=None):
        """Search Resident by their PCN."""
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pcn=pcn)
        self.check_object_permissions(request, obj)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    # @action(detail=True, methods=['GET'], url_path='qr')
    # def qr(self, request, pk=None):
    #     user = self.get_object()

    #     signed_message = sign_eddsa(user.info)

    #     qr = qrcode.make(base45.b45encode(signed_message))

    #     buffer = BytesIO()
    #     qr.save(buffer, format="PNG")
    #     buffer.seek(0)

    #     # qr.show()
    #     return HttpResponse(buffer, content_type="image/png")
    
    # @action(detail=True, methods=['GET'], url_path='id')
    # def id(self, request, pk=None):
    #     _id = self.get_object()

    #     # Load the ID template image
    #     id_image = Image.open(
    #         r'./identity/static/img/labs/ndsg-template.png'
    #     )

    #     # Initialize drawing context
    #     draw = ImageDraw.Draw(id_image)

    #     # Load the Roboto font
    #     font = ImageFont.truetype(
    #         r'./identity/static/fonts/Roboto/static/Roboto-Regular.ttf', 40
    #     )

    #     # Position of text and fields
    #     photo_x, photo_y =  62, 78                  # Coordinates for the photo position (top-left corner)
    #     photo_width, photo_height = 300, 400        # Photo size (width x height)

    #     # Add the fields on the ID template
    #     line_height = 50  # Line height for spacing between fields
    #     x_offset = 40  # Horizontal offset for text
    #     y_offset = photo_y  # Starting position for the fields below the photo

    #     fields = {
    #         # "Name": _id.name,
    #         # "Sex": _id.sex,
    #         "DOB": _id.birthdate,
    #         "ID": _id.id,
    #         "PCN": _id.pcn,
    #         "Verified": _id.verified
    #     }
        
    #     # Add each field text dynamically
    #     for label, value in fields.items():
    #         # Draw the label and value on the image
    #         draw.text((photo_x + photo_width + x_offset, y_offset), f"{label}: {value}", fill="black", font=font)
    #         y_offset += line_height  # Move to the next line

    #     # Save the updated image
    #     # id_image.show()
    #     buffer = BytesIO()
    #     id_image.save(buffer, format="PNG")
    #     buffer.seek(0)
        
    #     return HttpResponse(buffer, content_type="image/png")

class SectorViewset(viewsets.ModelViewSet):
    queryset = ResidentSector.objects.all()
    serializer_class = SectorSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj
