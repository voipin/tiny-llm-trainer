from django.db import models
from django.contrib.auth.models import User
from api_specs.models import OpenAPISpec


class SyntheticDataset(models.Model):
    name = models.CharField(max_length=200)
    spec = models.ForeignKey(OpenAPISpec, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    num_samples = models.IntegerField()
    generation_config = models.JSONField(default=dict)
    file_path = models.CharField(max_length=500)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.num_samples} samples)"


class TrainingRun(models.Model):
    name = models.CharField(max_length=200)
    dataset = models.ForeignKey(SyntheticDataset, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=200, default="HuggingFaceTB/SmolLM2-1.7B")
    training_config = models.JSONField(default=dict)
    output_dir = models.CharField(max_length=500)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    logs = models.TextField(blank=True)
    metrics = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"

    @property
    def duration(self):
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class TrainedModel(models.Model):
    name = models.CharField(max_length=200)
    training_run = models.OneToOneField(TrainingRun, on_delete=models.CASCADE)
    model_path = models.CharField(max_length=500)
    base_model = models.CharField(max_length=200)
    adapter_path = models.CharField(max_length=500, blank=True)
    model_size_mb = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (from {self.training_run.name})"
