'''
Django views for `identity` app.
'''


from django.contrib.auth.models import User, Group
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
import requests
import base64

from residents.models import Resident
from qr_manager.utils import read_qr, generate_qr
from mosip.models import MOSIPKYCResponse
from mosip.decorators import require_mosip

from .models import Resident, Sector
from .generator import generate_uid
from .serializers import (
    UserGroupSerializer, UserSerializer,
    ResidentSerializer, SectorSerializer
)
from .exceptions import DRFErrors


def _to_base64_image(image_bytes : bytes) -> str :
    return base64.b64encode(image_bytes).decode()


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
    
    @require_mosip()
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = {
            **request.POST.dict(),
            **request.FILES.dict()
        }

        name = data.get("full_name")
        if not name:
            first_name = data.get("first_name")
            middle_name = data.get("middle_name")
            last_name = data.get("last_name")
            suffix_name = data.get("suffix_name")
            name = (
                f"{first_name} {middle_name} {last_name}" if not suffix_name
                else f"{first_name} {middle_name} {last_name} {suffix_name}"
            )

        # Fetch user details from MOSIP
        uid = data.get("pcn")
        dob = data.get("date_of_birth")
        gender = data.get("gender")
        demographics = {
            "uid" : uid,
            "name" : name,
            "dob" :  dob,
            "gender" : gender,
        }
        required_fields = [
            key for key, value in demographics.items()
            if value is None
        ]
        if required_fields:
            return Response(
                {
                    "error"   : DRFErrors.FormMissingValue,
                    "details" : f"Missing values for: {', '.join(required_fields)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        mosip_response = MOSIPKYCResponse.from_demographics(uid=uid, name=name, dob=dob,
                                                            gender=gender)

        if mosip_response.errors:
            return Response(
                {
                    "error"   : DRFErrors.MOSIPAuthFailed,
                    "details" : mosip_response.error_messages
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate temporary UIN
        while True:
            temporary_uin = generate_uid()
            if not Resident.objects.filter(uin=temporary_uin).exists():
                break
        data["uin"] = temporary_uin
        
        # Create a response-safe image
        face_image = data.get("profile_image")
        if face_image:
            data["face_image"] = base64.b64encode(face_image).decode()
        else:
            data["face_image"] = mosip_response.user.face
        
        # Create QR
        try:
            image = generate_qr(**data)
            image_str = _to_base64_image(image)
        except Exception as err:
            return Response(
                {
                    "error"   : DRFErrors.QRGenerationFailed,
                    "details" : f"Encountered an error generating QR: {err}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Register Resident
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
                {
                    "error"   : DRFErrors.RegistrationFailed,
                    "details" : f"Encountered an error registering Resident: {err}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                "uin" : data.get("uin"),
                "qr" : image_str
            },
            status=status.HTTP_201_CREATED
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
                    "error" : DRFErrors.QRReaderFailed,
                    "details"   : f"Failed to read QR: {err}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_uin = payload.get("uin")
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
        
        user_uin = payload.get("uin")
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
