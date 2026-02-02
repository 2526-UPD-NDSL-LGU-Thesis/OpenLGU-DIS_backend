from django.urls import path, include
from rest_framework import routers
from . import views as api_views
from residents import views as resident_views

router = routers.DefaultRouter()
router.register(r'ids', resident_views.UserViewSet)

urlpatterns = [  
    path('', include(router.urls)),
    path('read/', api_views.read, name='read'),
]
