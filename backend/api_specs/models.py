from django.db import models
from django.contrib.auth.models import User
import json


class OpenAPISpec(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    spec_content = models.JSONField()
    version = models.CharField(max_length=50, default="3.0.0")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} v{self.version}"

    @property
    def endpoint_count(self):
        paths = self.spec_content.get('paths', {})
        count = 0
        for path_methods in paths.values():
            count += len([m for m in path_methods.keys() if m in ['get', 'post', 'put', 'delete', 'patch']])
        return count


class APIEndpoint(models.Model):
    spec = models.ForeignKey(OpenAPISpec, on_delete=models.CASCADE, related_name='endpoints')
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    operation_id = models.CharField(max_length=200, blank=True)
    summary = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict)
    request_body = models.JSONField(default=dict)
    responses = models.JSONField(default=dict)
    tags = models.JSONField(default=list)

    class Meta:
        unique_together = ['spec', 'path', 'method']
        ordering = ['path', 'method']

    def __str__(self):
        return f"{self.method.upper()} {self.path}"
