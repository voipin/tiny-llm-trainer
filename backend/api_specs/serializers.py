from rest_framework import serializers
from .models import OpenAPISpec, APIEndpoint


class OpenAPISpecSerializer(serializers.ModelSerializer):
    endpoint_count = serializers.ReadOnlyField()
    
    class Meta:
        model = OpenAPISpec
        fields = [
            'id', 'name', 'description', 'spec_content', 'version',
            'created_by', 'created_at', 'updated_at', 'is_active',
            'endpoint_count'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class APIEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIEndpoint
        fields = [
            'id', 'spec', 'path', 'method', 'operation_id',
            'summary', 'description', 'parameters', 'request_body',
            'responses', 'tags'
        ]