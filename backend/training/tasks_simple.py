from celery import shared_task
from django.conf import settings
import json
import os
from pathlib import Path
from datetime import datetime

from .models import SyntheticDataset, TrainingRun, TrainedModel
from api_specs.models import OpenAPISpec
from evaluation.models import EvaluationRun


@shared_task(bind=True)
def generate_synthetic_dataset(self, dataset_id: int):
    """Simple version for testing without ML dependencies"""
    try:
        dataset = SyntheticDataset.objects.get(id=dataset_id)
        dataset.status = 'generating'
        dataset.save()
        
        # Mock data generation for testing
        samples = [
            {
                'input': 'Get all pets',
                'output': '{"method": "GET", "url": "https://api.example.com/pets"}'
            },
            {
                'input': 'Create a new pet named Fluffy',
                'output': '{"method": "POST", "url": "https://api.example.com/pets", "body": {"name": "Fluffy"}}'
            }
        ]
        
        # Save mock dataset
        data_dir = Path(settings.DATA_DIR)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = data_dir / f"dataset_{dataset.id}.json"
        with open(output_path, 'w') as f:
            json.dump(samples, f, indent=2)
        
        # Update dataset
        dataset.file_path = str(output_path)
        dataset.status = 'completed'
        dataset.save()
        
        return {
            'status': 'success',
            'dataset_id': dataset_id,
            'num_samples': len(samples),
            'file_path': str(output_path)
        }
        
    except Exception as e:
        dataset = SyntheticDataset.objects.get(id=dataset_id)
        dataset.status = 'failed'
        dataset.save()
        
        return {
            'status': 'error',
            'dataset_id': dataset_id,
            'error': str(e)
        }


@shared_task(bind=True)
def train_model(self, training_run_id: int):
    """Simple version for testing without ML dependencies"""
    try:
        training_run = TrainingRun.objects.get(id=training_run_id)
        training_run.status = 'running'
        training_run.started_at = datetime.now()
        training_run.save()
        
        # Mock training
        import time
        time.sleep(2)  # Simulate training time
        
        # Mock metrics
        metrics = {
            'train_loss': 0.1234,
            'eval_loss': 0.2345,
            'train_runtime': 120.0,
            'epoch': 1.0
        }
        
        # Update training run
        training_run.status = 'completed'
        training_run.completed_at = datetime.now()
        training_run.metrics = metrics
        training_run.save()
        
        # Create mock trained model record
        trained_model = TrainedModel.objects.create(
            name=f"{training_run.name}_model",
            training_run=training_run,
            model_path=training_run.output_dir,
            base_model=training_run.model_name,
            adapter_path=training_run.output_dir,
            model_size_mb=100.0  # Mock size
        )
        
        return {
            'status': 'success',
            'training_run_id': training_run_id,
            'model_id': trained_model.id,
            'metrics': metrics
        }
        
    except Exception as e:
        training_run = TrainingRun.objects.get(id=training_run_id)
        training_run.status = 'failed'
        training_run.completed_at = datetime.now()
        training_run.logs = str(e)
        training_run.save()
        
        return {
            'status': 'error',
            'training_run_id': training_run_id,
            'error': str(e)
        }


@shared_task(bind=True)
def evaluate_model(self, evaluation_run_id: int):
    """Simple version for testing without ML dependencies"""
    try:
        evaluation_run = EvaluationRun.objects.get(id=evaluation_run_id)
        evaluation_run.status = 'running'
        evaluation_run.started_at = datetime.now()
        evaluation_run.save()
        
        # Mock evaluation
        import time
        time.sleep(3)  # Simulate evaluation time
        
        # Mock evaluation results
        results = {
            'exact_match': 0.85,
            'api_validity': 0.92,
            'method_accuracy': 0.95,
            'parameter_accuracy': 0.88,
            'bleu_score': 0.76,
            'total_samples': 100,
            'correct_samples': 85
        }
        
        # Update evaluation run
        evaluation_run.status = 'completed'
        evaluation_run.completed_at = datetime.now()
        evaluation_run.results = results
        evaluation_run.save()
        
        return {
            'status': 'success',
            'evaluation_run_id': evaluation_run_id,
            'results': results
        }
        
    except Exception as e:
        evaluation_run = EvaluationRun.objects.get(id=evaluation_run_id)
        evaluation_run.status = 'failed'
        evaluation_run.completed_at = datetime.now()
        evaluation_run.save()
        
        return {
            'status': 'error',
            'evaluation_run_id': evaluation_run_id,
            'error': str(e)
        }