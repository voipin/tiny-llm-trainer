from django.db import models
from django.contrib.auth.models import User
from training.models import TrainedModel, SyntheticDataset


class EvaluationRun(models.Model):
    name = models.CharField(max_length=200)
    model = models.ForeignKey(TrainedModel, on_delete=models.CASCADE)
    test_dataset = models.ForeignKey(SyntheticDataset, on_delete=models.CASCADE)
    evaluation_config = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    results = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"


class EvaluationMetric(models.Model):
    evaluation_run = models.ForeignKey(EvaluationRun, on_delete=models.CASCADE, related_name='metrics')
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_type = models.CharField(max_length=50, choices=[
        ('accuracy', 'Accuracy'),
        ('exact_match', 'Exact Match'),
        ('api_validity', 'API Validity'),
        ('parameter_accuracy', 'Parameter Accuracy'),
        ('method_accuracy', 'Method Accuracy'),
        ('path_accuracy', 'Path Accuracy'),
        ('bleu', 'BLEU Score'),
        ('rouge', 'ROUGE Score'),
    ])
    details = models.JSONField(default=dict)

    class Meta:
        unique_together = ['evaluation_run', 'metric_name']

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value:.4f}"


class EvaluationSample(models.Model):
    evaluation_run = models.ForeignKey(EvaluationRun, on_delete=models.CASCADE, related_name='samples')
    input_text = models.TextField()
    expected_output = models.TextField()
    predicted_output = models.TextField()
    is_correct = models.BooleanField()
    confidence_score = models.FloatField(null=True, blank=True)
    error_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Sample {self.id} - {'✓' if self.is_correct else '✗'}"
