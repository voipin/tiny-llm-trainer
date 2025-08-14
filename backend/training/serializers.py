from rest_framework import serializers
from .models import SyntheticDataset, TrainingRun, TrainedModel


class SyntheticDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyntheticDataset
        fields = [
            'id', 'name', 'spec', 'description', 'num_samples',
            'generation_config', 'file_path', 'created_by',
            'created_at', 'status'
        ]
        read_only_fields = ['created_by', 'created_at', 'file_path', 'status']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TrainingRunSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = TrainingRun
        fields = [
            'id', 'name', 'dataset', 'model_name', 'training_config',
            'output_dir', 'created_by', 'created_at', 'started_at',
            'completed_at', 'status', 'logs', 'metrics', 'duration'
        ]
        read_only_fields = [
            'created_by', 'created_at', 'started_at', 'completed_at',
            'status', 'logs', 'metrics'
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        # Set output directory
        if 'output_dir' not in validated_data:
            validated_data['output_dir'] = f"./models/training_run_{validated_data['name']}"
        return super().create(validated_data)


class TrainedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainedModel
        fields = [
            'id', 'name', 'training_run', 'model_path', 'base_model',
            'adapter_path', 'model_size_mb', 'created_at', 'is_active'
        ]