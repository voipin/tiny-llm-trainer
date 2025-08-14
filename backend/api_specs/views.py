import yaml
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import OpenAPISpec, APIEndpoint
from .serializers import OpenAPISpecSerializer, APIEndpointSerializer
from training.models import SyntheticDataset
from training.tasks_simple import generate_synthetic_dataset


class OpenAPISpecViewSet(viewsets.ModelViewSet):
    serializer_class = OpenAPISpecSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return OpenAPISpec.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        spec = serializer.save(created_by=self.request.user)
        
        # Parse and create endpoint records
        self._create_endpoints_from_spec(spec)
    
    def _create_endpoints_from_spec(self, spec):
        """Parse OpenAPI spec and create endpoint records"""
        # Parse spec_content if it's a string
        if isinstance(spec.spec_content, str):
            try:
                # Try JSON first
                spec_dict = json.loads(spec.spec_content)
            except json.JSONDecodeError:
                try:
                    # Try YAML
                    spec_dict = yaml.safe_load(spec.spec_content)
                except yaml.YAMLError:
                    # If both fail, skip endpoint creation
                    return
        else:
            spec_dict = spec.spec_content
            
        paths = spec_dict.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    APIEndpoint.objects.create(
                        spec=spec,
                        path=path,
                        method=method.upper(),
                        operation_id=details.get('operationId', ''),
                        summary=details.get('summary', ''),
                        description=details.get('description', ''),
                        parameters=details.get('parameters', []),
                        request_body=details.get('requestBody', {}),
                        responses=details.get('responses', {}),
                        tags=details.get('tags', [])
                    )
    
    @action(detail=True, methods=['post'])
    def generate_dataset(self, request, pk=None):
        """Generate synthetic dataset from this spec"""
        spec = self.get_object()
        
        # Get parameters
        name = request.data.get('name', f'{spec.name} Dataset')
        num_samples = request.data.get('num_samples', 1000)
        generation_config = request.data.get('generation_config', {})
        
        # Create dataset record
        dataset = SyntheticDataset.objects.create(
            name=name,
            spec=spec,
            num_samples=num_samples,
            generation_config=generation_config,
            file_path='',  # Will be set by task
            created_by=request.user,
            status='pending'
        )
        
        # Start generation task
        generate_synthetic_dataset.delay(dataset.id)
        
        return Response({
            'dataset_id': dataset.id,
            'status': 'pending',
            'message': 'Dataset generation started'
        })
    
    @action(detail=True, methods=['get'])
    def endpoints(self, request, pk=None):
        """Get endpoints for this spec"""
        spec = self.get_object()
        endpoints = APIEndpoint.objects.filter(spec=spec)
        serializer = APIEndpointSerializer(endpoints, many=True)
        return Response(serializer.data)
