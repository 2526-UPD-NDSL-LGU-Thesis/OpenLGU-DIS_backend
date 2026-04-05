'''
Top level router. Sends traffic out to frontend apps.
'''

from django.urls import path, include
from rest_framework import routers
from . import views as api_views
from residents import views as resident_views
from service import views as service_views

router = routers.DefaultRouter()
router.register(r'ids', resident_views.UserViewSet)
router.register(r'services', service_views.ServiceViewSet)

urlpatterns = [  
    path('', include(router.urls)),
    path('read/', api_views.read, name='read'),
    path('verify/', api_views.verify, name='verify'),
    path('startotp/', api_views.start_verify_otp, name='startotp'),
    path('otp/', api_views.verify_otp, name='otp'),
    path('digitalid/', api_views.digitalid, name='digitalid'),
    path('authenticate/', api_views.authenticate_message, name='authenticate'),
    path('claim/', api_views.claim, name='claim'),
    path('upload-qr/', api_views.upload_qr, name='upload-qr'),
    path('ping/', api_views.ping, name='ping')
]
