#!/usr/bin/env python3
"""
Example training script for SmolLM2 Task→API Mapper
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smollm_mapper.settings')

import django
django.setup()

from training.data_generation.synthetic_generator import SyntheticDataGenerator
from training.pipeline.smollm_trainer import SmolLMTrainer, TrainingConfig


def create_example_openapi_spec():
    """Create a simple example OpenAPI spec"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Pet Store API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "https://petstore.example.com/api/v1"}
        ],
        "paths": {
            "/pets": {
                "get": {
                    "summary": "List all pets",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "maximum": 100}
                        },
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["available", "pending", "sold"]}
                        }
                    ],
                    "responses": {"200": {"description": "A list of pets"}}
                },
                "post": {
                    "summary": "Create a pet",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "status": {"type": "string"},
                                        "category": {"type": "string"}
                                    },
                                    "required": ["name"]
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Pet created"}}
                }
            },
            "/pets/{petId}": {
                "get": {
                    "summary": "Get a pet by ID",
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {"200": {"description": "Pet details"}}
                },
                "put": {
                    "summary": "Update a pet",
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "status": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Pet updated"}}
                },
                "delete": {
                    "summary": "Delete a pet",
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {"204": {"description": "Pet deleted"}}
                }
            }
        }
    }


def main():
    print("🚀 SmolLM2 Task→API Mapper Example Training")
    
    # Create directories
    data_dir = Path("../data")
    models_dir = Path("../models")
    data_dir.mkdir(exist_ok=True)
    models_dir.mkdir(exist_ok=True)
    
    # Step 1: Generate synthetic data
    print("\n📊 Step 1: Generating synthetic training data...")
    
    spec = create_example_openapi_spec()
    generator = SyntheticDataGenerator(spec)
    
    # Generate training and validation datasets
    train_samples = generator.generate_synthetic_data(1000)
    val_samples = generator.generate_synthetic_data(200)
    
    train_path = data_dir / "train_dataset.json"
    val_path = data_dir / "val_dataset.json"
    
    generator.save_dataset(train_samples, str(train_path))
    generator.save_dataset(val_samples, str(val_path))
    
    print(f"✅ Generated {len(train_samples)} training samples")
    print(f"✅ Generated {len(val_samples)} validation samples")
    
    # Step 2: Configure training
    print("\n🧠 Step 2: Configuring SmolLM2 training...")
    
    config = TrainingConfig(
        model_name="HuggingFaceTB/SmolLM2-1.7B",
        output_dir=str(models_dir / "smollm2-petstore-api"),
        max_seq_length=1024,
        batch_size=2,  # Small batch for demo
        num_epochs=1,  # Quick training for demo
        learning_rate=2e-4,
        lora_r=8,
        lora_alpha=16,
        logging_steps=10,
        save_steps=100,
    )
    
    print(f"✅ Model: {config.model_name}")
    print(f"✅ Output: {config.output_dir}")
    print(f"✅ LoRA config: r={config.lora_r}, alpha={config.lora_alpha}")
    
    # Step 3: Train the model
    print("\n🏋️ Step 3: Training SmolLM2 model...")
    print("⚠️  This may take a while depending on your hardware...")
    
    try:
        trainer = SmolLMTrainer(config)
        metrics = trainer.train(
            dataset_path=str(train_path),
            eval_dataset_path=str(val_path)
        )
        
        print("✅ Training completed!")
        print(f"📊 Final metrics: {metrics}")
        
        # Step 4: Test the model
        print("\n🧪 Step 4: Testing the trained model...")
        
        test_prompts = [
            "Get all pets with status available",
            "Create a new pet named Fluffy",
            "Get pet with ID 123",
            "Update pet 456 with status sold",
            "Delete pet 789"
        ]
        
        for prompt in test_prompts:
            response = trainer.generate_response(prompt, max_length=256)
            print(f"\n📝 Input: {prompt}")
            print(f"🤖 Output: {response}")
        
        print("\n🎉 Example training completed successfully!")
        print(f"📁 Model saved to: {config.output_dir}")
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        print("💡 Make sure you have sufficient GPU memory and all dependencies installed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())