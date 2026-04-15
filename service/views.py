from django.http import HttpRequest, JsonResponse
from rest_framework import viewsets, status as HTTPStatus
from rest_framework.decorators import action, api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
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
def claim_service(request : HttpRequest, service_id : str) -> JsonResponse :
    data = request.data
    b45_qr = data.pop("qr")

    status, payload = validate_qr(b45_qr)
    
    if not status:
        return JsonResponse(
            payload,
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )

    try:
        service = Service.objects.get(name=service_id)
    except Service.DoesNotExist:
        return JsonResponse(
            { "error" : "Service does not exist" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )
    
    user_uin = payload[169][99]
    try:
        resident = User.objects.get(uin=user_uin)
    except User.DoesNotExist:
        return JsonResponse(
            { "error" : "User does not exist" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    success = claim(
        user=resident,
        service=service,
        amount=1,
        claimed_by=authenticated_user
    )

    if not success:
        return JsonResponse(
            { "error" : "Failed to claim service" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )

    return JsonResponse(
        { "status" : "Service claimed" },
        status=HTTPStatus.HTTP_201_CREATED
    )



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def claim_service_with_pcn(request : HttpRequest, service_id : str) -> JsonResponse :
    data = request.data
    b45_qr = data.pop("qr")

    payload = read_qr(b45_qr)

    if not payload:
        return JsonResponse(
            { "error" : "Failed to parse QR" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )

    try:
        service = Service.objects.get(name=service_id)
    except Service.DoesNotExist:
        return JsonResponse(
            { "error" : "Service does not exist" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )
    
    user_pcn = payload[169]["sb"]["PCN"]
    try:
        resident = User.objects.get(pcn=user_pcn)
    except User.DoesNotExist:
        return JsonResponse(
            { "error" : "User does not exist" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )
    
    authenticated_user = request.user

    success = claim(
        user=resident,
        service=service,
        amount=1,
        claimed_by=authenticated_user
    )

    if not success:
        return JsonResponse(
            { "error" : "Failed to claim service" },
            status=HTTPStatus.HTTP_400_BAD_REQUEST
        )

    return JsonResponse(
        { "status" : "Service claimed" },
        status=HTTPStatus.HTTP_201_CREATED
    )