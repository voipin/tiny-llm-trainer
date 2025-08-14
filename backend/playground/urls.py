from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaygroundSessionViewSet, PlaygroundQueryViewSet

router = DefaultRouter()
router.register(r'playground/sessions', PlaygroundSessionViewSet, basename='playground-session')
router.register(r'playground/queries', PlaygroundQueryViewSet, basename='playground-query')

urlpatterns = [
    path('', include(router.urls)),
    path('playground/generate/', PlaygroundQueryViewSet.as_view({'post': 'generate'}), name='playground-generate'),
]