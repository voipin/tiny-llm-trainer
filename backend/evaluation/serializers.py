from rest_framework import serializers
from .models import EvaluationRun, EvaluationMetric, EvaluationSample


class EvaluationMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationMetric
        fields = ['id', 'metric_name', 'metric_value', 'metric_type', 'details']


class EvaluationSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationSample
        fields = [
            'id', 'input_text', 'expected_output', 'predicted_output',
            'is_correct', 'confidence_score', 'error_details', 'created_at'
        ]


class EvaluationRunSerializer(serializers.ModelSerializer):
    metrics = EvaluationMetricSerializer(many=True, read_only=True)
    
    class Meta:
        model = EvaluationRun
        fields = [
            'id', 'name', 'model', 'test_dataset', 'evaluation_config',
            'created_by', 'created_at', 'started_at', 'completed_at',
            'status', 'results', 'metrics'
        ]
        read_only_fields = [
            'created_by', 'created_at', 'started_at', 'completed_at',
            'status', 'results'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)