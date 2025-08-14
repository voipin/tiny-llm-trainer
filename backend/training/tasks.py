from celery import shared_task
from django.conf import settings
import json
import os
from pathlib import Path
from datetime import datetime

from .models import SyntheticDataset, TrainingRun, TrainedModel
from .data_generation.synthetic_generator import SyntheticDataGenerator
from .pipeline.smollm_trainer import SmolLMTrainer, TrainingConfig
from api_specs.models import OpenAPISpec


@shared_task(bind=True)
def generate_synthetic_dataset(self, dataset_id: int):
    try:
        dataset = SyntheticDataset.objects.get(id=dataset_id)
        dataset.status = 'generating'
        dataset.save()
        
        # Get the OpenAPI spec
        spec = dataset.spec
        
        # Initialize generator
        generator = SyntheticDataGenerator(spec.spec_content)
        
        # Generate samples
        samples = generator.generate_synthetic_data(dataset.num_samples)
        
        # Save dataset
        data_dir = Path(settings.DATA_DIR)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = data_dir / f"dataset_{dataset.id}.json"
        generator.save_dataset(samples, str(output_path))
        
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
    try:
        training_run = TrainingRun.objects.get(id=training_run_id)
        training_run.status = 'running'
        training_run.started_at = datetime.now()
        training_run.save()
        
        # Get dataset
        dataset = training_run.dataset
        if not dataset.file_path or not os.path.exists(dataset.file_path):
            raise ValueError("Dataset file not found")
        
        # Setup training config
        config = TrainingConfig(
            model_name=training_run.model_name,
            output_dir=training_run.output_dir,
            **training_run.training_config
        )
        
        # Initialize trainer
        trainer = SmolLMTrainer(config)
        
        # Start training
        metrics = trainer.train(dataset.file_path)
        
        # Update training run
        training_run.status = 'completed'
        training_run.completed_at = datetime.now()
        training_run.metrics = metrics
        training_run.save()
        
        # Create trained model record
        model_size = 0
        if os.path.exists(config.output_dir):
            model_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(config.output_dir)
                for filename in filenames
            ) / (1024 * 1024)  # Convert to MB
        
        trained_model = TrainedModel.objects.create(
            name=f"{training_run.name}_model",
            training_run=training_run,
            model_path=config.output_dir,
            base_model=config.model_name,
            adapter_path=config.output_dir,
            model_size_mb=model_size
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