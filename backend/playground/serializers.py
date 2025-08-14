from rest_framework import serializers
from .models import PlaygroundSession, PlaygroundQuery


class PlaygroundSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaygroundSession
        fields = [
            'id', 'name', 'model', 'spec', 'created_by',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PlaygroundQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaygroundQuery
        fields = [
            'id', 'session', 'input_text', 'generated_output',
            'parsed_api_call', 'is_valid_api', 'validation_errors',
            'generation_time_ms', 'created_at'
        ]