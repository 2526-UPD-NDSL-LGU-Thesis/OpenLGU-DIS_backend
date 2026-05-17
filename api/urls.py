'''
Top level router. Sends traffic out to frontend apps.
'''

from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from . import views as api_views

from residents import views as resident_views
from service import views as service_views


# pylint: disable=trailing-whitespace


router = routers.DefaultRouter()
router.register(r'ids', resident_views.ResidentViewSet)
router.register(r'users', resident_views.UserViewSet)
router.register(r'groups', resident_views.UserGroupViewSet)
router.register(r'services', service_views.ServiceViewSet)
router.register(r'servicegroups', service_views.ServiceGroupViewSet, basename='servicegroup')
router.register(r'claims', service_views.ServiceClaimViewSet)
router.register(r'sectors', resident_views.SectorViewset)

urlpatterns = [  
    path('', include(router.urls)),
    path('', include('mosip.urls')),
    path('', include('qr_manager.urls')),
    path('', include('service.urls')),
    path('login/', api_views.login_view),
    path('ping/', api_views.ping),
    path('user/ping/', api_views.user_ping),
    path('csrf/', api_views.get_csrf),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
