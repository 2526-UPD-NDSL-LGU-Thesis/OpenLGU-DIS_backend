from django.http import HttpRequest
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Service, claim
from .serializers import ServiceSerializer
from residents.models import User
from qr_manager import validate_qr, read_qr


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list: Return all services
    retrieve: Return a single service
    active: Return only active services
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        active_services = self.queryset.filter(active=True)
        serializer = self.get_serializer(active_services, many=True)
        return Response(serializer.data)


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def claim_service(request : HttpRequest, service_id : str) -> Response :
    data = request.data
    b45_qr = data.pop("qr")

    _status, payload = validate_qr(b45_qr)
    
    if not _status:
        return Response(
            payload,
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        service = Service.objects.get(name=service_id)
    except Service.DoesNotExist:
        return Response(
            { "error" : "Service does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user_uin = payload[169][99]
    try:
        resident = User.objects.get(uin=user_uin)
    except User.DoesNotExist:
        return Response(
            { "error" : "User does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    res, err = claim(
        user=resident,
        service=service,
        amount=1,
        claimed_by=authenticated_user
    )

    if not res:
        return Response(
            err,
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        { "status" : "Service claimed" },
        status=status.HTTP_201_CREATED
    )



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def claim_service_with_pcn(request : HttpRequest, service_id : str) -> Response :
    data = request.data
    b45_qr = data.pop("qr")

    payload = read_qr(b45_qr)

    if not payload:
        return Response(
            { "error" : "Failed to parse QR" },
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
        resident = User.objects.get(pcn=user_pcn)
    except User.DoesNotExist:
        return Response(
            { "error" : "User does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    success = claim(
        user=resident,
        service=service,
        amount=1,
        claimed_by=authenticated_user
    )

    if not success:
        return Response(
            { "error" : "Failed to claim service" },
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        { "status" : "Service claimed" },
        status=status.HTTP_201_CREATED
    )
