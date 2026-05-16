from django.http import HttpRequest
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Service, Claim, Assignment
from .permissions import CanAccessServiceClaim
from .serializers import ServiceSerializer, ClaimSerializer
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
            )
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
    

@permission_classes([CanAccessServiceClaim, IsAuthenticated])
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


@api_view(["POST"])
# @permission_classes([IsAuthenticated]) TODO re-place
def claim_service(request : HttpRequest, service_id : str) -> Response :
    data = request.data
    b45_qr = data.pop("qr")

    try:
        type, payload = read_qr(b45_qr).values()
    except Exception as err:
        return Response(
            { "error" : f"Failed to read QR: {err}" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if type != QRTypes.OpenLGUQR:
        return Response(
            { "error" : f"Invalid QR Type. Expected {QRTypes.OpenLGUQR}, got {type}." },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return Response(
            { "error" : "Service does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user_uin = payload[169][75]
    try:
        resident = Resident.objects.get(uin=user_uin)
    except Resident.DoesNotExist:
        return Response(
            { "error" : "User does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    result, error = service.claim(
        resident=resident,
        amount=1,
        claimed_by=authenticated_user
    )

    if not result:
        return Response(
            error,
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        { "status" : "Service claimed" },
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
# @permission_classes([IsAuthenticated]) TODO re-place
def claim_service_with_pcn(request : HttpRequest, service_id : str) -> Response :
    data = request.data
    b45_qr = data.pop("qr")

    type, payload = read_qr(b45_qr).values()

    try:
        type, payload = read_qr(b45_qr).values()
    except Exception as err:
        return Response(
            { "error" : f"Failed to read QR: {err}" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if type != QRTypes.PhilSysTemporaryQR:
        return Response(
            { "error" : f"Invalid QR Type. Expected {QRTypes.PhilSysTemporaryQR}, got {type}." },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        service = Service.objects.get(name=service_id)
    except Service.DoesNotExist:
        return Response(
            { "error" : "Service does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user_pcn = payload[169]["sb"]["PCN"]
    try:
        resident = Resident.objects.get(pcn=user_pcn)
    except Resident.DoesNotExist:
        return Response(
            { "error" : "User does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    result, error = service.claim(
        resident=resident,
        amount=1,
        claimed_by=authenticated_user
    )

    if not result:
        return Response(
            error,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    #TODO: Return the object created

    return Response(
        { "status" : "Service claimed" },
        status=status.HTTP_201_CREATED
    )
