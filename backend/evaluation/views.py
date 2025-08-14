from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import EvaluationRun
from .serializers import EvaluationRunSerializer
from training.tasks_simple import evaluate_model


class EvaluationRunViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationRunSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return EvaluationRun.objects.filter(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start evaluation"""
        evaluation_run = self.get_object()
        
        if evaluation_run.status != 'pending':
            return Response(
                {'error': 'Evaluation already started or completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start evaluation task
        evaluate_model.delay(evaluation_run.id)
        
        return Response({'status': 'starting'})
