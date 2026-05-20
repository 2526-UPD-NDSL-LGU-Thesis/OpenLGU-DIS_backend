'''
Django views for `identity` app.
'''

from pathlib import Path

from django.contrib.auth.models import User, Group
from django.core.files import File
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
from PIL import Image
from io import BytesIO
import base64

from residents.models import Resident
from qr_manager.utils import read_qr, generate_qr

from .models import Resident, Sector
from .generator import generate_uid
from .serializers import UserGroupSerializer, UserSerializer, ResidentSerializer, SectorSerializer
from .exceptions import DRFErrors


POR_FILE = Path(r"C:\Users\J4M3S\Desktop\MOSIP\OpenLGU-DIS_backend\residents\sample\proof.pdf")
IMG_FILE = Path(r"C:\Users\J4M3S\Desktop\MOSIP\OpenLGU-DIS_backend\residents\sample\citizen_3_compressed.jpg")


def _to_base64_image(image_bytes : bytes) -> str :
    return base64.b64encode(image_bytes).decode()


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

    @action(detail=False, methods=['GET'], url_path='me')
    def get_me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


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
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = {
            **request.POST.dict(),
            **request.FILES.dict()
        }

        while True:
            temporary_uin = generate_uid()
            if not Resident.objects.filter(uin=temporary_uin).exists():
                break
        data["uin"] = temporary_uin
        
        face_image = data.get("profile_image")
        if face_image:
            data["face_image"] = base64.b64encode(face_image.read()).decode()
        
        try:
            image = generate_qr(**data)
            image_str = _to_base64_image(image)
        except Exception as err:
            return Response(
                { "details" : f"Encountered an error generating QR: {err}" },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            resident = Resident.objects.create(
                pcn=data.get("pcn"),
                uin=temporary_uin,
                proof_of_residence=data.get("proof_of_residence"),
                profile_image=data.get("profile_image"),
            )
            data["uin"] = resident.uin
        except Exception as err:
            return Response(
                { "details" : f"Encountered an error registering Resident: {err}" },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data.pop("proof_of_residence")
        data.pop("profile_image")
        return Response(
            {
                "id_details" : data,
                "qr" : image_str
            }
        )
    
    @action(detail=False, methods=['GET'], url_path=r"pcn/(?P<pcn>[^/.]+)")
    def by_pcn(self, request, pcn=None):
        """Search Resident by their PCN."""
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pcn=pcn)
        self.check_object_permissions(request, obj)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='enlist')
    def sector_enlist(self, request):
        # queryset = self.filter_queryset(self.get_queryset())
        # resident = get_object_or_404(queryset, uin=uin)
        # self.check_object_permissions(request, resident)

        qr = request.data.get("qr")

        if not qr:
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "Expected qr, got None instead."
            })
        
        try:
            _, payload = read_qr(qr).values()
        except Exception as err:
            return Response(
                {
                    "errpr" : DRFErrors.QRReaderFailed,
                    "details"   : f"Failed to read QR: {err}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_uin = payload[169][75]
        try:
            resident = Resident.objects.get(uin=user_uin)
        except Resident.DoesNotExist:
            return Response(
                {
                    "details" : "Resident does not exist." 
                },
                status=status.HTTP_400_BAD_REQUEST
        )
        
        sectors = request.data.get("sector")

        if not sectors:
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "Expected sector, got None instead."
            })
        
        if not isinstance(sectors, list):
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : f"sector should be a list, not type {type(sectors)}."
            })
        
        if len(sectors) == 0:
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "sector should not be empty."
            })

        sector_list = [
            get_object_or_404(Sector, id=sector_id) for sector_id in sectors
        ]
        
        resident.sector.add(*sector_list)

        serializer = self.get_serializer(resident)
        return Response(serializer.data)


    @action(detail=False, methods=['POST'], url_path='delist')
    def sector_delist(self, request):
        # queryset = self.filter_queryset(self.get_queryset())
        # resident = get_object_or_404(queryset, uin=uin)
        # self.check_object_permissions(request, resident)

        qr = request.data.get("qr")

        if not qr:
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "Expected qr, got None instead."
            })
        
        try:
            _, payload = read_qr(qr).values()
        except Exception as err:
            return Response(
                {
                    "errpr" : DRFErrors.QRReaderFailed,
                    "details"   : f"Failed to read QR: {err}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_uin = payload[169][75]
        try:
            resident = Resident.objects.get(uin=user_uin)
        except Resident.DoesNotExist:
            return Response(
                {
                    "details" : "Resident does not exist." 
                },
                status=status.HTTP_400_BAD_REQUEST
        )
        
        sectors = request.data.get("sector")

        if not sectors:
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "Expected sector, got None instead."
            })
        
        if not isinstance(sectors, list):
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : f"sector should be a list, not type {type(sectors)}."
            })
        
        if len(sectors) == 0:
            return Response({
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "sector should not be empty."
            })

        sector_list = [
            get_object_or_404(Sector, id=sector_id) for sector_id in sectors
        ]
        
        resident.sector.remove(*sector_list)

        serializer = self.get_serializer(resident)
        return Response(serializer.data)

class SectorViewset(viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj
