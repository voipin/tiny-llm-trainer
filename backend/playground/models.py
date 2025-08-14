from django.db import models
from django.contrib.auth.models import User
from training.models import TrainedModel
from api_specs.models import OpenAPISpec


class PlaygroundSession(models.Model):
    name = models.CharField(max_length=200)
    model = models.ForeignKey(TrainedModel, on_delete=models.CASCADE)
    spec = models.ForeignKey(OpenAPISpec, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.model.name})"


class PlaygroundQuery(models.Model):
    session = models.ForeignKey(PlaygroundSession, on_delete=models.CASCADE, related_name='queries')
    input_text = models.TextField()
    generated_output = models.TextField()
    parsed_api_call = models.JSONField(default=dict)
    is_valid_api = models.BooleanField(null=True, blank=True)
    validation_errors = models.JSONField(default=list)
    generation_time_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Query {self.id} - {self.input_text[:50]}..."
