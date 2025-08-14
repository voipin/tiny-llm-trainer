from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpenAPISpecViewSet

router = DefaultRouter()
router.register(r'specs', OpenAPISpecViewSet, basename='openapi-spec')

urlpatterns = [
    path('', include(router.urls)),
]