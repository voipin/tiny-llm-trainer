import os
from django.http import HttpResponse, Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import SyntheticDataset, TrainingRun, TrainedModel
from .serializers import SyntheticDatasetSerializer, TrainingRunSerializer, TrainedModelSerializer
from .tasks_simple import generate_synthetic_dataset, train_model


class SyntheticDatasetViewSet(viewsets.ModelViewSet):
    serializer_class = SyntheticDatasetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SyntheticDataset.objects.filter(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Start dataset generation"""
        dataset = self.get_object()
        
        if dataset.status != 'pending':
            return Response(
                {'error': 'Dataset generation already started or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start generation task
        generate_synthetic_dataset.delay(dataset.id)
        
        dataset.status = 'generating'
        dataset.save()
        
        return Response({'status': 'generating'})
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download dataset file"""
        dataset = self.get_object()
        
        if dataset.status != 'completed':
            return Response(
                {'error': 'Dataset is not ready for download'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not dataset.file_path or not os.path.exists(dataset.file_path):
            return Response(
                {'error': 'Dataset file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            with open(dataset.file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/json')
                response['Content-Disposition'] = f'attachment; filename="{dataset.name}.json"'
                return response
        except Exception as e:
            return Response(
                {'error': f'Failed to download dataset: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def create_training_run(self, request, pk=None):
        """Create a training run from this dataset"""
        dataset = self.get_object()
        
        if dataset.status != 'completed':
            return Response(
                {'error': 'Dataset is not ready for training'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get training parameters
        name = request.data.get('name', f'{dataset.name} Training')
        training_config = request.data.get('config', {})
        
        # Create training run
        training_run = TrainingRun.objects.create(
            name=name,
            dataset=dataset,
            training_config=training_config,
            output_dir=f'./models/{name.lower().replace(" ", "_")}',
            created_by=request.user,
            status='pending'
        )
        
        serializer = TrainingRunSerializer(training_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TrainingRunViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingRunSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TrainingRun.objects.filter(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start training"""
        training_run = self.get_object()
        
        if training_run.status != 'pending':
            return Response(
                {'error': 'Training already started or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if dataset is ready
        if training_run.dataset.status != 'completed':
            return Response(
                {'error': 'Dataset is not ready for training'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start training task
        train_model.delay(training_run.id)
        
        return Response({'status': 'starting'})
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop training"""
        training_run = self.get_object()
        
        if training_run.status != 'running':
            return Response(
                {'error': 'Training is not currently running'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement training cancellation
        training_run.status = 'cancelled'
        training_run.save()
        
        return Response({'status': 'cancelled'})


class TrainedModelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrainedModelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TrainedModel.objects.filter(
            training_run__created_by=self.request.user
        )
