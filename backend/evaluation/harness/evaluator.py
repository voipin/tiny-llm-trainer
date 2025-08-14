import json
import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs
import difflib
from collections import defaultdict

import jsonschema
from openapi_spec_validator import validate_spec


@dataclass
class EvaluationResult:
    sample_id: int
    input_text: str
    expected_output: str
    predicted_output: str
    is_correct: bool
    confidence_score: float
    error_details: Dict[str, Any]
    metrics: Dict[str, float]


@dataclass
class EvaluationMetrics:
    exact_match: float
    api_validity: float
    method_accuracy: float
    path_accuracy: float
    parameter_accuracy: float
    json_validity: float
    semantic_similarity: float
    bleu_score: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'exact_match': self.exact_match,
            'api_validity': self.api_validity,
            'method_accuracy': self.method_accuracy,
            'path_accuracy': self.path_accuracy,
            'parameter_accuracy': self.parameter_accuracy,
            'json_validity': self.json_validity,
            'semantic_similarity': self.semantic_similarity,
            'bleu_score': self.bleu_score,
        }


class APICallEvaluator:
    def __init__(self, openapi_spec: Dict[str, Any]):
        self.spec = openapi_spec
        self.base_url = self._extract_base_url()
        self.valid_endpoints = self._extract_valid_endpoints()
        
    def _extract_base_url(self) -> str:
        servers = self.spec.get('servers', [])
        if servers:
            return servers[0].get('url', 'https://api.example.com')
        return 'https://api.example.com'
    
    def _extract_valid_endpoints(self) -> Dict[str, List[str]]:
        endpoints = defaultdict(list)
        paths = self.spec.get('paths', {})
        
        for path, methods in paths.items():
            for method in methods.keys():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoints[path].append(method.upper())
        
        return dict(endpoints)
    
    def evaluate_single_sample(self, 
                             input_text: str, 
                             expected_output: str, 
                             predicted_output: str,
                             sample_id: int = 0) -> EvaluationResult:
        
        error_details = {}
        metrics = {}
        
        # Parse expected and predicted API calls
        try:
            expected_api = self._parse_api_call(expected_output)
            expected_valid = True
        except Exception as e:
            expected_api = None
            expected_valid = False
            error_details['expected_parse_error'] = str(e)
        
        try:
            predicted_api = self._parse_api_call(predicted_output)
            predicted_valid = True
        except Exception as e:
            predicted_api = None
            predicted_valid = False
            error_details['predicted_parse_error'] = str(e)
        
        # Calculate metrics
        metrics['exact_match'] = float(expected_output.strip() == predicted_output.strip())
        metrics['json_validity'] = float(predicted_valid)
        
        if expected_valid and predicted_valid:
            metrics.update(self._calculate_api_metrics(expected_api, predicted_api))
        else:
            metrics.update({
                'api_validity': 0.0,
                'method_accuracy': 0.0,
                'path_accuracy': 0.0,
                'parameter_accuracy': 0.0,
            })
        
        # Calculate semantic similarity
        metrics['semantic_similarity'] = self._calculate_semantic_similarity(
            expected_output, predicted_output
        )
        
        # Calculate BLEU score
        metrics['bleu_score'] = self._calculate_bleu_score(
            expected_output, predicted_output
        )
        
        # Determine if correct (weighted combination of metrics)
        is_correct = self._determine_correctness(metrics)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(metrics)
        
        return EvaluationResult(
            sample_id=sample_id,
            input_text=input_text,
            expected_output=expected_output,
            predicted_output=predicted_output,
            is_correct=is_correct,
            confidence_score=confidence_score,
            error_details=error_details,
            metrics=metrics
        )
    
    def evaluate_dataset(self, 
                        test_samples: List[Dict[str, str]],
                        predictions: List[str]) -> Tuple[List[EvaluationResult], EvaluationMetrics]:
        
        if len(test_samples) != len(predictions):
            raise ValueError("Number of test samples and predictions must match")
        
        results = []
        
        for i, (sample, prediction) in enumerate(zip(test_samples, predictions)):
            result = self.evaluate_single_sample(
                input_text=sample['input'],
                expected_output=sample['output'],
                predicted_output=prediction,
                sample_id=i
            )
            results.append(result)
        
        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(results)
        
        return results, aggregate_metrics
    
    def _parse_api_call(self, api_call_str: str) -> Dict[str, Any]:
        # Try to parse as JSON
        try:
            return json.loads(api_call_str.strip())
        except json.JSONDecodeError:
            # Try to extract JSON from text
            json_match = re.search(r'\{.*\}', api_call_str, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("Could not parse API call as JSON")
    
    def _calculate_api_metrics(self, expected: Dict[str, Any], predicted: Dict[str, Any]) -> Dict[str, float]:
        metrics = {}
        
        # Method accuracy
        expected_method = expected.get('method', '').upper()
        predicted_method = predicted.get('method', '').upper()
        metrics['method_accuracy'] = float(expected_method == predicted_method)
        
        # URL/Path accuracy
        expected_url = expected.get('url', '')
        predicted_url = predicted.get('url', '')
        
        # Extract paths from URLs
        expected_path = self._extract_path_from_url(expected_url)
        predicted_path = self._extract_path_from_url(predicted_url)
        
        metrics['path_accuracy'] = self._calculate_path_similarity(expected_path, predicted_path)
        
        # Parameter accuracy (query params and body)
        expected_query = expected.get('query', {})
        predicted_query = predicted.get('query', {})
        expected_body = expected.get('body', {})
        predicted_body = predicted.get('body', {})
        
        query_accuracy = self._calculate_dict_similarity(expected_query, predicted_query)
        body_accuracy = self._calculate_dict_similarity(expected_body, predicted_body)
        
        metrics['parameter_accuracy'] = (query_accuracy + body_accuracy) / 2
        
        # API validity (check against OpenAPI spec)
        metrics['api_validity'] = float(self._validate_against_spec(predicted))
        
        return metrics
    
    def _extract_path_from_url(self, url: str) -> str:
        if not url:
            return ''
        
        try:
            parsed = urlparse(url)
            return parsed.path
        except:
            return url
    
    def _calculate_path_similarity(self, expected: str, predicted: str) -> float:
        if expected == predicted:
            return 1.0
        
        # Normalize paths
        expected = expected.strip('/').split('/')
        predicted = predicted.strip('/').split('/')
        
        if len(expected) != len(predicted):
            return 0.0
        
        matches = 0
        for exp_part, pred_part in zip(expected, predicted):
            # Handle path parameters
            if exp_part.startswith('{') and exp_part.endswith('}'):
                matches += 1  # Path parameters always match
            elif exp_part == pred_part:
                matches += 1
        
        return matches / len(expected) if expected else 0.0
    
    def _calculate_dict_similarity(self, expected: Dict, predicted: Dict) -> float:
        if not expected and not predicted:
            return 1.0
        
        if not expected or not predicted:
            return 0.0
        
        expected_keys = set(expected.keys())
        predicted_keys = set(predicted.keys())
        
        # Key similarity
        key_intersection = expected_keys & predicted_keys
        key_union = expected_keys | predicted_keys
        key_similarity = len(key_intersection) / len(key_union) if key_union else 1.0
        
        # Value similarity for common keys
        value_matches = 0
        for key in key_intersection:
            if expected[key] == predicted[key]:
                value_matches += 1
        
        value_similarity = value_matches / len(key_intersection) if key_intersection else 0.0
        
        return (key_similarity + value_similarity) / 2
    
    def _validate_against_spec(self, api_call: Dict[str, Any]) -> bool:
        try:
            method = api_call.get('method', '').upper()
            url = api_call.get('url', '')
            path = self._extract_path_from_url(url)
            
            # Check if endpoint exists in spec
            for spec_path, methods in self.valid_endpoints.items():
                if self._path_matches_spec(path, spec_path) and method in methods:
                    return True
            
            return False
        except:
            return False
    
    def _path_matches_spec(self, actual_path: str, spec_path: str) -> bool:
        # Simple path matching with parameter substitution
        actual_parts = actual_path.strip('/').split('/')
        spec_parts = spec_path.strip('/').split('/')
        
        if len(actual_parts) != len(spec_parts):
            return False
        
        for actual_part, spec_part in zip(actual_parts, spec_parts):
            if spec_part.startswith('{') and spec_part.endswith('}'):
                continue  # Parameter match
            elif actual_part != spec_part:
                return False
        
        return True
    
    def _calculate_semantic_similarity(self, expected: str, predicted: str) -> float:
        # Simple character-level similarity
        return difflib.SequenceMatcher(None, expected, predicted).ratio()
    
    def _calculate_bleu_score(self, expected: str, predicted: str) -> float:
        # Simplified BLEU score calculation
        expected_tokens = expected.split()
        predicted_tokens = predicted.split()
        
        if not expected_tokens or not predicted_tokens:
            return 0.0
        
        # 1-gram precision
        expected_set = set(expected_tokens)
        predicted_set = set(predicted_tokens)
        
        intersection = expected_set & predicted_set
        precision = len(intersection) / len(predicted_set) if predicted_set else 0.0
        
        # Brevity penalty
        bp = min(1.0, len(predicted_tokens) / len(expected_tokens))
        
        return bp * precision
    
    def _determine_correctness(self, metrics: Dict[str, float]) -> bool:
        # Weighted combination of metrics
        weights = {
            'exact_match': 0.3,
            'api_validity': 0.25,
            'method_accuracy': 0.15,
            'path_accuracy': 0.15,
            'parameter_accuracy': 0.15,
        }
        
        score = sum(metrics.get(metric, 0.0) * weight for metric, weight in weights.items())
        return score >= 0.7  # Threshold for correctness
    
    def _calculate_confidence(self, metrics: Dict[str, float]) -> float:
        # Average of key metrics
        key_metrics = ['json_validity', 'api_validity', 'method_accuracy', 'path_accuracy']
        valid_metrics = [metrics.get(m, 0.0) for m in key_metrics if m in metrics]
        
        return sum(valid_metrics) / len(valid_metrics) if valid_metrics else 0.0
    
    def _calculate_aggregate_metrics(self, results: List[EvaluationResult]) -> EvaluationMetrics:
        if not results:
            return EvaluationMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        # Calculate averages
        metrics_sum = defaultdict(float)
        for result in results:
            for metric, value in result.metrics.items():
                metrics_sum[metric] += value
        
        n = len(results)
        
        return EvaluationMetrics(
            exact_match=metrics_sum['exact_match'] / n,
            api_validity=metrics_sum['api_validity'] / n,
            method_accuracy=metrics_sum['method_accuracy'] / n,
            path_accuracy=metrics_sum['path_accuracy'] / n,
            parameter_accuracy=metrics_sum['parameter_accuracy'] / n,
            json_validity=metrics_sum['json_validity'] / n,
            semantic_similarity=metrics_sum['semantic_similarity'] / n,
            bleu_score=metrics_sum['bleu_score'] / n,
        )