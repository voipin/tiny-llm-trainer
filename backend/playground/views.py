from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import time
import json

from .models import PlaygroundSession, PlaygroundQuery
from .serializers import PlaygroundSessionSerializer, PlaygroundQuerySerializer
from training.models import TrainedModel
from api_specs.models import OpenAPISpec


class PlaygroundSessionViewSet(viewsets.ModelViewSet):
    serializer_class = PlaygroundSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PlaygroundSession.objects.filter(created_by=self.request.user)


class PlaygroundQueryViewSet(viewsets.ModelViewSet):
    serializer_class = PlaygroundQuerySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PlaygroundQuery.objects.filter(
            session__created_by=self.request.user
        )
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate API call from natural language"""
        model_id = request.data.get('model_id')
        spec_id = request.data.get('spec_id')
        input_text = request.data.get('input_text')
        
        if not all([model_id, spec_id, input_text]):
            return Response(
                {'error': 'model_id, spec_id, and input_text are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            model = TrainedModel.objects.get(id=model_id)
            spec = OpenAPISpec.objects.get(id=spec_id)
        except (TrainedModel.DoesNotExist, OpenAPISpec.DoesNotExist):
            return Response(
                {'error': 'Model or spec not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create session
        session, created = PlaygroundSession.objects.get_or_create(
            model=model,
            spec=spec,
            created_by=request.user,
            defaults={'name': f'{model.name} + {spec.name}'}
        )
        
        # TODO: Implement actual model inference
        # For now, return a mock response
        start_time = time.time()
        
        # Mock API call generation
        generated_output = json.dumps({
            "method": "GET",
            "url": f"https://api.example.com/users",
            "query": {"limit": 10, "status": "active"}
        }, indent=2)
        
        generation_time = int((time.time() - start_time) * 1000)
        
        # Create query record
        query = PlaygroundQuery.objects.create(
            session=session,
            input_text=input_text,
            generated_output=generated_output,
            parsed_api_call=json.loads(generated_output),
            is_valid_api=True,
            generation_time_ms=generation_time
        )
        
        serializer = self.get_serializer(query)
        return Response(serializer.data)
