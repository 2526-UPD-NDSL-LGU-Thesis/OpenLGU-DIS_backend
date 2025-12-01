'''
Django views for `identity` app.
'''

from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from .models import CompSciLabID, CompSciDeptID, CompSciLabs
from .serializers import CompSciLabIDSerializer, CompSciDeptIDSerializer, CompSciLabsSerializer

__all__ = (
    'profile',
    'CompSciLabIDViewSet',
    'CompSciDeptIDViewSet',
    'CompSciLabsViewSet',
)

def profile(request) -> HttpResponse :
    '''Render profile page.'''
    return render(request, "profile.html")

class CompSciLabIDViewSet(viewsets.ModelViewSet):
    '''View set for `CompSciLabID`.'''
    http_method_names = ['get', 'post']
    permission_classes = [AllowAny]
    queryset = CompSciLabID.objects.all()
    serializer_class = CompSciLabIDSerializer


class CompSciDeptIDViewSet(viewsets.ModelViewSet):
    '''View set for `CompSciDeptID`.'''
    http_method_names = ['get', 'post']
    permission_classes = [AllowAny]
    queryset = CompSciDeptID.objects.all()
    serializer_class = CompSciDeptIDSerializer


class CompSciLabsViewSet(viewsets.ModelViewSet):
    '''View set for `CompSciLabs`.'''
    http_method_names = ['get']
    permission_classes = [AllowAny]
    queryset = CompSciLabs.objects.all()
    serializer_class = CompSciLabsSerializer