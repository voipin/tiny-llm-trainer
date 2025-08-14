from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvaluationRunViewSet

router = DefaultRouter()
router.register(r'evaluation-runs', EvaluationRunViewSet, basename='evaluation-run')

urlpatterns = [
    path('', include(router.urls)),
]