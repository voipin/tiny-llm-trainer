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
        
        # Use actual model inference
        start_time = time.time()
        
        try:
            from .inference import get_inference
            inference = get_inference()
            
            # Get spec content for context
            spec_content = spec.spec_content if hasattr(spec, 'spec_content') else None
            
            # Generate API call using the trained model
            result = inference.generate_api_call(model_id, input_text, spec_content)
            
            generated_output = result['generated_output']
            parsed_api_call = result['parsed_api_call']
            is_valid_api = result.get('is_valid_json', True)
            
        except Exception as e:
            # Fallback to basic mock if inference fails
            generated_output = json.dumps({
                "method": "GET",
                "url": f"https://api.example.com/fallback",
                "query": {"error": f"Inference failed: {str(e)}"}
            }, indent=2)
            parsed_api_call = json.loads(generated_output)
            is_valid_api = True
        
        generation_time = int((time.time() - start_time) * 1000)
        
        # Create query record
        query = PlaygroundQuery.objects.create(
            session=session,
            input_text=input_text,
            generated_output=generated_output,
            parsed_api_call=parsed_api_call,
            is_valid_api=is_valid_api,
            generation_time_ms=generation_time
        )
        
        serializer = self.get_serializer(query)
        return Response(serializer.data)
