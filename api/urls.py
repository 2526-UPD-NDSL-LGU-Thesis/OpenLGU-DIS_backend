from django.urls import path, include
from rest_framework import routers
from . import views as api_views
from identity import views as identity_views

router = routers.DefaultRouter()
router.register(r'labs', identity_views.CompSciLabsViewSet)
router.register(r'ids', identity_views.CompSciLabIDViewSet)
router.register(r'deptids', identity_views.CompSciDeptIDViewSet)

urlpatterns = [  
    path('', include(router.urls)),
    path('read/', api_views.read, name='read'),
]
