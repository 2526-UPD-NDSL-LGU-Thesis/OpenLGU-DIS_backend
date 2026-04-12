from django.http import HttpRequest, JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Service, claim
from .serializers import ServiceSerializer
from residents.models import User


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


@api_view(["POST"])
def claim_service(request : HttpRequest, service_id : str) -> JsonResponse :
    data = request.data

    try:
        service = Service.objects.get(service__name=service_id)
    except Service.DoesNotExist:
        return JsonResponse(
            { "error" : "Service does not exist" },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user_uin = data["user_uin"]
    try:
        resident = User.objects.get(pk=user_uin)
    except User.DoesNotExist:
        return JsonResponse(
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
        return JsonResponse(
            { "error" : "Failed to claim service" },
            status=status.HTTP_400_BAD_REQUEST
        )

    return JsonResponse(
        { "status" : "Service claimed" },
        status=status.HTTP_201_CREATED
    )
