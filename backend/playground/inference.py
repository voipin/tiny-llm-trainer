"""
Model inference utilities for the playground
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from training.pipeline.smollm_trainer import SmolLMTrainer, TrainingConfig
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from training.models import TrainedModel


class ModelInference:
    """Handle model loading and inference for playground"""
    
    def __init__(self):
        self._loaded_models = {}  # Cache loaded models
    
    def generate_api_call(self, model_id: int, prompt: str, spec_content: str = None) -> Dict[str, Any]:
        """Generate API call from natural language prompt"""
        try:
            # Get model info from database
            trained_model = TrainedModel.objects.get(id=model_id, is_active=True)
            
            if ML_AVAILABLE:
                # TODO: Implement actual model inference when ML libraries are available
                # For now, generate a more intelligent mock response based on the prompt
                response = self._generate_smart_mock(prompt, spec_content, trained_model)
            else:
                # Generate smart mock response without ML libraries
                response = self._generate_smart_mock(prompt, spec_content, trained_model)
            
            # Try to parse as JSON
            try:
                parsed_response = json.loads(response)
                is_valid_json = True
            except json.JSONDecodeError:
                parsed_response = {"raw_output": response}
                is_valid_json = False
            
            return {
                "generated_output": response,
                "parsed_api_call": parsed_response,
                "is_valid_json": is_valid_json,
                "model_loaded": ML_AVAILABLE,
                "model_name": trained_model.name,
                "base_model": trained_model.base_model
            }
            
        except Exception as e:
            # Fallback to basic mock response
            return {
                "generated_output": json.dumps({
                    "method": "GET",
                    "url": "https://api.example.com/error",
                    "error": f"Failed to process request: {str(e)}"
                }, indent=2),
                "parsed_api_call": {
                    "method": "GET", 
                    "url": "https://api.example.com/error",
                    "error": f"Failed to process request: {str(e)}"
                },
                "is_valid_json": True,
                "model_loaded": False,
                "error": str(e)
            }
    
    def _generate_smart_mock(self, prompt: str, spec_content: str, trained_model) -> str:
        """Generate a smarter mock response based on prompt analysis"""
        prompt_lower = prompt.lower()
        
        # Analyze prompt for HTTP method
        if any(word in prompt_lower for word in ['create', 'add', 'new', 'post']):
            method = "POST"
        elif any(word in prompt_lower for word in ['update', 'modify', 'change', 'put', 'patch']):
            method = "PUT"
        elif any(word in prompt_lower for word in ['delete', 'remove']):
            method = "DELETE"
        else:
            method = "GET"
        
        # Analyze prompt for endpoint
        if 'pet' in prompt_lower:
            if 'compliment' in prompt_lower:
                url = "https://api.petcompliments.com/v1/compliments"
                if method == "GET":
                    # Extract pet type if mentioned
                    for pet_type in ['cat', 'dog', 'hamster', 'fish', 'bird']:
                        if pet_type in prompt_lower:
                            url += f"/{pet_type}"
                            break
                    else:
                        url += "/cat"  # default
            else:
                url = "https://api.example.com/pets"
        elif 'user' in prompt_lower:
            url = "https://api.example.com/users"
        else:
            url = "https://api.example.com/items"
        
        # Build response based on method
        response = {"method": method, "url": url}
        
        # Add parameters based on prompt
        if method == "GET":
            query_params = {}
            if 'limit' in prompt_lower:
                # Try to extract number
                import re
                limit_match = re.search(r'limit (\d+)', prompt_lower)
                if limit_match:
                    query_params['limit'] = int(limit_match.group(1))
                else:
                    query_params['limit'] = 10
            
            if 'status' in prompt_lower:
                if 'active' in prompt_lower:
                    query_params['status'] = 'active'
                elif 'pending' in prompt_lower:
                    query_params['status'] = 'pending'
                elif 'completed' in prompt_lower:
                    query_params['status'] = 'completed'
            
            if 'mood' in prompt_lower:
                for mood in ['happy', 'sleepy', 'playful', 'grumpy']:
                    if mood in prompt_lower:
                        query_params['mood'] = mood
                        break
            
            if query_params:
                response['query'] = query_params
                
        elif method in ["POST", "PUT"]:
            body = {}
            if 'name' in prompt_lower:
                # Try to extract name
                import re
                name_match = re.search(r'name (\w+)', prompt_lower)
                if name_match:
                    body['name'] = name_match.group(1)
                else:
                    body['name'] = 'Fluffy'
            
            if 'email' in prompt_lower:
                import re
                email_match = re.search(r'email (\S+@\S+)', prompt_lower)
                if email_match:
                    body['email'] = email_match.group(1)
            
            if 'compliment' in prompt_lower:
                body['customCompliment'] = "You're an amazing pet!"
                body['petType'] = 'cat'
            
            if body:
                response['body'] = body
        
        return json.dumps(response, indent=2)


# Global inference instance
_inference = ModelInference()


def get_inference() -> ModelInference:
    """Get the global inference instance"""
    return _inference