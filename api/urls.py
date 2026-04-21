'''
Top level router. Sends traffic out to frontend apps.
'''

from django.urls import path, include
from rest_framework import routers
from residents import views as resident_views
from service import views as service_views

from . import views as api_views

# pylint: disable=trailing-whitespace

router = routers.DefaultRouter()
router.register(r'ids', resident_views.UserViewSet)
router.register(r'services', service_views.ServiceViewSet)

urlpatterns = [  
    path('', include(router.urls)),
    path('', include('mosip.urls')),
    path('', include('qr_manager.urls')),
    path('', include('service.urls')),
    path('login/', api_views.login_view),
    path('ping/', api_views.ping),
    path('user/ping/', api_views.user_ping),
    path('csrf/', api_views.get_csrf),
]
