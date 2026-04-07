from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Service
from .serializers import ServiceSerializer


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