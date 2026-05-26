from django.http import HttpRequest
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Service, Claim, Assignment
from .models import Group as AssignmentGroup
from .permissions import HasServiceClaimRole
from .serializers import ServiceSerializer, ClaimSerializer, GroupSerializer
from .exceptions import DRFErrors
from mosip.models import MOSIPAuthResponse
from residents.models import Resident
from qr_manager import read_qr, QRTypes


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Service.objects.all()
    
        assignment = Assignment.objects.filter(user=user).first()

        if assignment:
            return Service.objects.filter(
                allowed_groups__in=assignment.groups.all()
            ).distinct()
        else:
            return []

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=False, methods=['get'])
    def active(self, request):
        active_services = self.queryset.filter(active=True)
        serializer = self.get_serializer(active_services, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def claims(self, request, pk=None):
        service = self.get_object()
        claims = service.claims.all()
        serializer = ClaimSerializer(claims, many=True)
        return Response(serializer.data)
    

@permission_classes([HasServiceClaimRole])
class ServiceClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Claim.objects.none()
        
        if user.is_superuser:
            return Claim.objects.all()

        return Claim.objects.filter(
            claimed_by=user
        ).distinct()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj
    
    def perform_create(self, serializer):
        user = self.request.user
        service = serializer.validated_data['service']

        if not service.allowed_groups.filter(id__in=user.groups.all()).exists():
            raise PermissionDenied("You cannot claim this service.")
        
        serializer.save(user=user, claimed_by=user)


@permission_classes([HasServiceClaimRole])
class ServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = AssignmentGroup.objects.all()
    serializer_class = GroupSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

@api_view(["POST"])
@permission_classes([HasServiceClaimRole])
def claim_service(request : HttpRequest, service_id : str) -> Response :
    data = request.data

    b45_qr = data.get("qr")
    if not b45_qr:
        return Response(
            {
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "Expected 'qr', got None instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        qr_type, payload = read_qr(b45_qr).values()
    except Exception as err:
        return Response(
            {
                "error"   : DRFErrors.QRVerificationFailed,
                "details" : str(err)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if qr_type != QRTypes.OpenLGUQR:
        return Response(
            {
                "error"   : DRFErrors.InvalidQRType,
                "details" : f"Expected {QRTypes.OpenLGUQR}, got {qr_type} instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return Response(
            {
                "error"   : DRFErrors.ServiceDoesNotExist, 
                "details" : f"Service {service_id} does not exist."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uin = payload.get("uin")
    try:
        resident = Resident.objects.get(uin=uin)
    except Resident.DoesNotExist:
        return Response(
            {
                "errors"  : DRFErrors.ResidentDoesNotExist,
                "details" : f"User {uin} does not exist."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    result, body = service.claim(
        resident=resident,
        amount=1,
        claimed_by=authenticated_user
    )

    if not result:
        return Response(
            body,
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        ClaimSerializer(body["body"]).data,
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([HasServiceClaimRole])
def claim_service_with_pcn(request : HttpRequest, service_id : str) -> Response :
    data = request.data
    
    b45_qr = data.get("qr")
    if not b45_qr:
        return Response(
            {
                "error"   : DRFErrors.InvalidPOSTBody,
                "details" : "Expected 'qr', got None instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        qr_type, payload = read_qr(b45_qr).values()
    except Exception as err:
        return Response(
            {
                "error"   : DRFErrors.QRVerificationFailed,
                "details" : str(err)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if qr_type == QRTypes.OpenLGUQR:
        return Response(
            {
                "error"   : DRFErrors.InvalidQRType,
                "details" : f"Expected a PhilSys or eGovPH QR code, got {QRTypes.OpenLGUQR} \
                    instead."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return Response(
            {
                "error"   : DRFErrors.ServiceDoesNotExist, 
                "details" : f"Service {service_id} does not exist."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # uid = payload.get("pcn")
    # name = payload.get("full_name")
    # dob = payload.get("date_of_birth")
    # gender = payload.get("gender")
    # demographics = {
    #     "uid" : uid,
    #     "name" : name,
    #     "dob" :  dob,
    #     "gender" : gender,
    # }
    # required_fields = [
    #     key for key, value in demographics.items()
    #     if value is None
    # ]
    # if required_fields:
    #     return Response(
    #         {
    #             "error"   : DRFErrors.MOSIPMissingValues,
    #             "details" : f"QR code is missing the required values for KYC: \
    #                 {', '.join(required_fields)}"
    #         },
    #         status=status.HTTP_400_BAD_REQUEST
    #     )
    # mosip_response = MOSIPAuthResponse.from_demographics(uid=uid, name=name, dob=dob,
    #                                                     gender=gender)

    # if mosip_response.errors:
    #     return Response(
    #         {
    #             "error"   : DRFErrors.MOSIPAuthFailed,
    #             "details" : mosip_response.error_messages
    #         },
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    # if not mosip_response.response.status:
    #     return Response(
    #         {
    #             "error"   : DRFErrors.MOSIPAuthFailed,
    #             "details" : "MOSIP Authentication failed."
    #         },
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    try:
        resident = Resident.objects.get(pcn=pcn)
    except Resident.DoesNotExist:
        return Response(
            {
                "errors"  : DRFErrors.ResidentDoesNotExist,
                "details" : f"User {pcn} does not exist."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    result, body = service.claim(
        resident=resident,
        amount=1,
        claimed_by=authenticated_user
    )

    if not result:
        return Response(
            body,
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        ClaimSerializer(body["body"]).data,
        status=status.HTTP_201_CREATED
    )
