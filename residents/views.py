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
from .exceptions import DRFErrors


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
    
    @action(detail=False, methods=['GET'], url_path=r"pcn/(?P<pcn>[^/.]+)")
    def by_pcn(self, request, pcn=None):
        """Search Resident by their PCN."""
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pcn=pcn)
        self.check_object_permissions(request, obj)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='enlist')
    def sector_enlist(self, request, uin=None):
        queryset = self.filter_queryset(self.get_queryset())
        resident = get_object_or_404(queryset, uin=uin)
        self.check_object_permissions(request, resident)
        
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
            get_object_or_404(ResidentSector, id=sector_id) for sector_id in sectors
        ]
        
        resident.sector.add(*sector_list)

        serializer = self.get_serializer(resident)
        return Response(serializer.data)


    @action(detail=True, methods=['POST'], url_path='delist')
    def sector_delist(self, request, uin=None):
        queryset = self.filter_queryset(self.get_queryset())
        resident = get_object_or_404(queryset, uin=uin)
        self.check_object_permissions(request, resident)
        
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
            get_object_or_404(ResidentSector, id=sector_id) for sector_id in sectors
        ]
        
        resident.sector.remove(*sector_list)

        serializer = self.get_serializer(resident)
        return Response(serializer.data)

class SectorViewset(viewsets.ModelViewSet):
    queryset = ResidentSector.objects.all()
    serializer_class = SectorSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj
    