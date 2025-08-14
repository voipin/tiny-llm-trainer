import json
import random
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class APICall:
    method: str
    url: str
    path: str
    query_params: Dict[str, Any]
    body: Dict[str, Any]
    headers: Dict[str, str]


class SyntheticDataGenerator:
    def __init__(self, openapi_spec: Dict[str, Any]):
        self.spec = openapi_spec
        self.base_url = self._extract_base_url()
        self.endpoints = self._parse_endpoints()
        
        # Templates for natural language requests
        self.request_templates = [
            "Get {resource} with {param}",
            "Create a new {resource} with {fields}",
            "Update {resource} {id} with {fields}",
            "Delete {resource} {id}",
            "List all {resource}",
            "Search for {resource} where {condition}",
            "Fetch {resource} details for {param}",
            "Add {resource} to {parent}",
            "Remove {resource} from {parent}",
            "Get {resource} by {param}",
        ]
        
        # Common parameter values
        self.sample_values = {
            'id': ['123', '456', 'abc-123', 'user-456'],
            'name': ['John Doe', 'Jane Smith', 'Product A', 'Service B'],
            'email': ['john@example.com', 'jane@example.com'],
            'status': ['active', 'inactive', 'pending'],
            'type': ['premium', 'basic', 'enterprise'],
            'category': ['electronics', 'books', 'clothing'],
            'limit': [10, 20, 50, 100],
            'offset': [0, 10, 20],
            'page': [1, 2, 3],
            'sort': ['name', 'date', 'price'],
            'order': ['asc', 'desc'],
        }

    def _extract_base_url(self) -> str:
        servers = self.spec.get('servers', [])
        if servers:
            return servers[0].get('url', 'https://api.example.com')
        return 'https://api.example.com'

    def _parse_endpoints(self) -> List[Dict[str, Any]]:
        endpoints = []
        paths = self.spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'details': details,
                        'parameters': details.get('parameters', []),
                        'requestBody': details.get('requestBody', {}),
                        'summary': details.get('summary', ''),
                        'tags': details.get('tags', []),
                    })
        
        return endpoints

    def generate_synthetic_data(self, num_samples: int) -> List[Dict[str, str]]:
        samples = []
        
        for _ in range(num_samples):
            endpoint = random.choice(self.endpoints)
            
            # Generate natural language request
            nl_request = self._generate_natural_language_request(endpoint)
            
            # Generate corresponding API call
            api_call = self._generate_api_call(endpoint)
            
            # Format as training sample
            sample = {
                'input': nl_request,
                'output': self._format_api_call(api_call),
                'endpoint_info': {
                    'path': endpoint['path'],
                    'method': endpoint['method'],
                    'summary': endpoint['summary'],
                }
            }
            
            samples.append(sample)
        
        return samples

    def _generate_natural_language_request(self, endpoint: Dict[str, Any]) -> str:
        method = endpoint['method'].lower()
        path = endpoint['path']
        summary = endpoint['summary']
        tags = endpoint.get('tags', [])
        
        # Extract resource name from path or tags
        resource = self._extract_resource_name(path, tags)
        
        # Generate based on HTTP method
        if method == 'get':
            if '{id}' in path or '{' in path:
                return f"Get {resource} details for {self._generate_param_description(endpoint)}"
            else:
                return f"List all {resource}"
        
        elif method == 'post':
            fields = self._generate_field_description(endpoint)
            return f"Create a new {resource} with {fields}"
        
        elif method == 'put' or method == 'patch':
            fields = self._generate_field_description(endpoint)
            return f"Update {resource} with {fields}"
        
        elif method == 'delete':
            return f"Delete {resource} {self._generate_param_description(endpoint)}"
        
        # Fallback to summary if available
        if summary:
            return summary
        
        return f"{method.title()} {resource}"

    def _extract_resource_name(self, path: str, tags: List[str]) -> str:
        if tags:
            return tags[0].lower()
        
        # Extract from path
        parts = [p for p in path.split('/') if p and not p.startswith('{')]
        if parts:
            return parts[-1].rstrip('s')  # Remove plural 's'
        
        return 'resource'

    def _generate_param_description(self, endpoint: Dict[str, Any]) -> str:
        parameters = endpoint.get('parameters', [])
        path_params = [p for p in parameters if p.get('in') == 'path']
        
        if path_params:
            param = path_params[0]
            param_name = param['name']
            sample_value = self._get_sample_value(param_name, param.get('schema', {}))
            return f"{param_name} {sample_value}"
        
        return "ID 123"

    def _generate_field_description(self, endpoint: Dict[str, Any]) -> str:
        request_body = endpoint.get('requestBody', {})
        if not request_body:
            return "the required fields"
        
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        schema = json_content.get('schema', {})
        
        properties = schema.get('properties', {})
        if properties:
            fields = list(properties.keys())[:3]  # Take first 3 fields
            return ', '.join(fields)
        
        return "the required fields"

    def _generate_api_call(self, endpoint: Dict[str, Any]) -> APICall:
        method = endpoint['method']
        path = endpoint['path']
        
        # Generate path parameters
        filled_path = path
        path_params = {}
        parameters = endpoint.get('parameters', [])
        
        for param in parameters:
            if param.get('in') == 'path':
                param_name = param['name']
                sample_value = self._get_sample_value(param_name, param.get('schema', {}))
                filled_path = filled_path.replace(f'{{{param_name}}}', str(sample_value))
                path_params[param_name] = sample_value
        
        # Generate query parameters
        query_params = {}
        for param in parameters:
            if param.get('in') == 'query' and random.random() < 0.3:  # 30% chance
                param_name = param['name']
                sample_value = self._get_sample_value(param_name, param.get('schema', {}))
                query_params[param_name] = sample_value
        
        # Generate request body
        body = {}
        request_body = endpoint.get('requestBody', {})
        if request_body and method.upper() in ['POST', 'PUT', 'PATCH']:
            body = self._generate_request_body(request_body)
        
        # Generate headers
        headers = {'Content-Type': 'application/json'}
        
        return APICall(
            method=method,
            url=self.base_url + filled_path,
            path=filled_path,
            query_params=query_params,
            body=body,
            headers=headers
        )

    def _get_sample_value(self, param_name: str, schema: Dict[str, Any]) -> Any:
        param_type = schema.get('type', 'string')
        param_format = schema.get('format', '')
        
        # Check if we have predefined samples for this parameter name
        if param_name.lower() in self.sample_values:
            return random.choice(self.sample_values[param_name.lower()])
        
        # Generate based on type
        if param_type == 'integer':
            return random.randint(1, 1000)
        elif param_type == 'number':
            return round(random.uniform(1.0, 100.0), 2)
        elif param_type == 'boolean':
            return random.choice([True, False])
        elif param_type == 'array':
            return [self._get_sample_value('item', schema.get('items', {}))]
        else:  # string
            if param_format == 'email':
                return random.choice(self.sample_values['email'])
            elif param_format == 'date':
                return '2024-01-15'
            elif param_format == 'date-time':
                return '2024-01-15T10:30:00Z'
            else:
                return f"sample_{param_name}"

    def _generate_request_body(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        content = request_body.get('content', {})
        json_content = content.get('application/json', {})
        schema = json_content.get('schema', {})
        
        return self._generate_object_from_schema(schema)

    def _generate_object_from_schema(self, schema: Dict[str, Any]) -> Any:
        schema_type = schema.get('type', 'object')
        
        if schema_type == 'object':
            obj = {}
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            for prop_name, prop_schema in properties.items():
                # Include required fields and 50% of optional fields
                if prop_name in required or random.random() < 0.5:
                    obj[prop_name] = self._generate_object_from_schema(prop_schema)
            
            return obj
        
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            return [self._generate_object_from_schema(items_schema)]
        
        else:
            return self._get_sample_value('field', schema)

    def _format_api_call(self, api_call: APICall) -> str:
        result = {
            'method': api_call.method,
            'url': api_call.url,
        }
        
        if api_call.query_params:
            result['query'] = api_call.query_params
        
        if api_call.body:
            result['body'] = api_call.body
        
        if api_call.headers and len(api_call.headers) > 1:  # More than just Content-Type
            result['headers'] = api_call.headers
        
        return json.dumps(result, indent=2)

    def save_dataset(self, samples: List[Dict[str, str]], output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(samples, f, indent=2)

    def save_dataset_jsonl(self, samples: List[Dict[str, str]], output_path: str) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for sample in samples:
                f.write(json.dumps(sample) + '\n')