from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SyntheticDatasetViewSet, TrainingRunViewSet, TrainedModelViewSet

router = DefaultRouter()
router.register(r'datasets', SyntheticDatasetViewSet, basename='dataset')
router.register(r'training-runs', TrainingRunViewSet, basename='training-run')
router.register(r'models', TrainedModelViewSet, basename='trained-model')

urlpatterns = [
    path('', include(router.urls)),
]