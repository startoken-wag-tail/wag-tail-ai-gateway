"""
External Load Balancer Provider
Allows customers to use their own LLM infrastructure
"""

import aiohttp
import json
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class ExternalLBProvider:
    """Provider for customer-managed load balancers and LLM farms"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize external LB provider
        
        Config structure:
        {
            "endpoint": "https://customer-lb.example.com/v1/completions",
            "auth_type": "bearer|api_key|oauth2|mtls|custom",
            "auth_token": "token-here",
            "custom_headers": {},
            "request_format": "openai|anthropic|custom",
            "response_format": "openai|anthropic|custom",
            "timeout": 120,
            "verify_ssl": true
        }
        """
        self.endpoint = config.get('endpoint')
        self.auth_type = config.get('auth_type', 'bearer')
        self.auth_token = config.get('auth_token')
        self.custom_headers = config.get('custom_headers', {})
        self.request_format = config.get('request_format', 'openai')
        self.response_format = config.get('response_format', 'openai')
        self.timeout = config.get('timeout', 120)
        self.verify_ssl = config.get('verify_ssl', True)
        self.retry_config = config.get('retry', {
            'max_attempts': 3,
            'backoff_base': 2,
            'max_backoff': 60
        })
        
        # Request/Response transformers
        self.request_transformer = self._get_request_transformer()
        self.response_transformer = self._get_response_transformer()
        
        # Metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_latency': 0
        }
    
    def _get_request_transformer(self):
        """Get appropriate request transformer based on format"""
        transformers = {
            'openai': self._transform_request_openai,
            'anthropic': self._transform_request_anthropic,
            'custom': self._transform_request_custom
        }
        return transformers.get(self.request_format, self._transform_request_openai)
    
    def _get_response_transformer(self):
        """Get appropriate response transformer based on format"""
        transformers = {
            'openai': self._transform_response_openai,
            'anthropic': self._transform_response_anthropic,
            'custom': self._transform_response_custom
        }
        return transformers.get(self.response_format, self._transform_response_openai)
    
    async def generate(self, 
                       messages: list,
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 1000,
                       stream: bool = False,
                       **kwargs) -> Dict[str, Any]:
        """
        Generate completion using customer's load balancer
        """
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        # Transform request to customer's format
        request_body = self.request_transformer(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
        
        # Build headers
        headers = self._build_headers()
        
        # Make request with retries
        for attempt in range(self.retry_config['max_attempts']):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        headers=headers,
                        json=request_body,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        ssl=self.verify_ssl
                    ) as response:
                        response.raise_for_status()
                        
                        if stream:
                            return self._handle_stream_response(response)
                        else:
                            response_data = await response.json()
                            
                            # Transform response to standard format
                            transformed = self.response_transformer(response_data)
                            
                            # Record metrics
                            latency = time.time() - start_time
                            self.metrics['successful_requests'] += 1
                            self.metrics['total_latency'] += latency
                            
                            # Add metadata
                            transformed['_metadata'] = {
                                'provider': 'external_lb',
                                'endpoint': self.endpoint,
                                'latency_ms': latency * 1000,
                                'attempt': attempt + 1
                            }
                            
                            return transformed
                            
            except aiohttp.ClientResponseError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                if e.status == 429:  # Rate limit
                    await self._exponential_backoff(attempt)
                elif e.status >= 500:  # Server error
                    await self._exponential_backoff(attempt)
                else:
                    raise  # Client error, don't retry
                    
            except Exception as e:
                logger.error(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt == self.retry_config['max_attempts'] - 1:
                    self.metrics['failed_requests'] += 1
                    raise
                await self._exponential_backoff(attempt)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers based on auth type"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Wag-Tail-Gateway/1.0'
        }
        
        # Add custom headers
        headers.update(self.custom_headers)
        
        # Add authentication
        if self.auth_type == 'bearer':
            headers['Authorization'] = f'Bearer {self.auth_token}'
        elif self.auth_type == 'api_key':
            headers['X-API-Key'] = self.auth_token
        elif self.auth_type == 'oauth2':
            # OAuth2 token should be refreshed separately
            headers['Authorization'] = f'Bearer {self.auth_token}'
        elif self.auth_type == 'custom':
            # Custom auth handled via custom_headers
            pass
        
        return headers
    
    def _transform_request_openai(self, **kwargs) -> Dict:
        """Transform to OpenAI-compatible format"""
        return {
            'model': kwargs.get('model', 'gpt-3.5-turbo'),
            'messages': kwargs.get('messages', []),
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 1000),
            'stream': kwargs.get('stream', False)
        }
    
    def _transform_request_anthropic(self, **kwargs) -> Dict:
        """Transform to Anthropic-compatible format"""
        messages = kwargs.get('messages', [])
        # Convert messages to Anthropic format
        prompt = "\n\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in messages
        ])
        
        return {
            'prompt': prompt,
            'model': kwargs.get('model', 'claude-2'),
            'max_tokens_to_sample': kwargs.get('max_tokens', 1000),
            'temperature': kwargs.get('temperature', 0.7)
        }
    
    def _transform_request_custom(self, **kwargs) -> Dict:
        """Custom transformation - override in subclass"""
        return kwargs
    
    def _transform_response_openai(self, response: Dict) -> Dict:
        """Transform from OpenAI format to standard format"""
        return {
            'content': response['choices'][0]['message']['content'],
            'model': response.get('model'),
            'usage': response.get('usage', {}),
            'finish_reason': response['choices'][0].get('finish_reason'),
            'raw_response': response
        }
    
    def _transform_response_anthropic(self, response: Dict) -> Dict:
        """Transform from Anthropic format to standard format"""
        return {
            'content': response['completion'],
            'model': response.get('model'),
            'usage': {
                'prompt_tokens': response.get('prompt_token_count', 0),
                'completion_tokens': response.get('completion_token_count', 0),
                'total_tokens': response.get('total_token_count', 0)
            },
            'finish_reason': response.get('stop_reason'),
            'raw_response': response
        }
    
    def _transform_response_custom(self, response: Dict) -> Dict:
        """Custom transformation - override in subclass"""
        return response
    
    async def _exponential_backoff(self, attempt: int):
        """Exponential backoff for retries"""
        backoff = min(
            self.retry_config['backoff_base'] ** attempt,
            self.retry_config['max_backoff']
        )
        await asyncio.sleep(backoff)
    
    async def _handle_stream_response(self, response):
        """Handle streaming responses"""
        async for chunk in response.content:
            # Parse SSE or newline-delimited JSON
            if chunk:
                yield self._parse_stream_chunk(chunk)
    
    def _parse_stream_chunk(self, chunk: bytes) -> Dict:
        """Parse streaming chunk"""
        try:
            # Try to parse as JSON
            data = json.loads(chunk.decode('utf-8').strip())
            return self.response_transformer(data)
        except:
            return {'content': chunk.decode('utf-8'), 'stream': True}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of customer's endpoint"""
        try:
            health_endpoint = self.endpoint.replace('/completions', '/health')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_endpoint,
                    headers=self._build_headers(),
                    timeout=aiohttp.ClientTimeout(total=5),
                    ssl=self.verify_ssl
                ) as response:
                    return {
                        'healthy': response.status == 200,
                        'status_code': response.status,
                        'endpoint': self.endpoint,
                        'metrics': self.metrics
                    }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'endpoint': self.endpoint,
                'metrics': self.metrics
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get provider metrics"""
        avg_latency = 0
        if self.metrics['successful_requests'] > 0:
            avg_latency = (self.metrics['total_latency'] / 
                          self.metrics['successful_requests']) * 1000
        
        return {
            'provider': 'external_lb',
            'endpoint': self.endpoint,
            'total_requests': self.metrics['total_requests'],
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'average_latency_ms': avg_latency,
            'success_rate': (self.metrics['successful_requests'] / 
                           max(self.metrics['total_requests'], 1)) * 100
        }


class CustomProviderPlugin(ABC):
    """Base class for customer-specific provider plugins"""
    
    @abstractmethod
    def transform_request(self, wag_tail_request: Dict) -> Dict:
        """Transform Wag-Tail request format to customer format"""
        pass
    
    @abstractmethod
    def transform_response(self, customer_response: Dict) -> Dict:
        """Transform customer response format to Wag-Tail format"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict) -> bool:
        """Validate customer configuration"""
        pass