"""
Provider health caching using Redis for shared state across instances.
Validates configurations and maintains only healthy providers in fallback chain.
"""

import redis
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from wag_tail_logger import logger

class ProviderHealthCache:
    """
    Redis-based cache for LLM provider health status.
    Shared across all gateway instances.
    """
    
    def __init__(self, redis_client=None, ttl_seconds: int = 300):
        """
        Initialize health cache with Redis backend.
        
        Args:
            redis_client: Redis client instance (uses DB 2 for metrics)
            ttl_seconds: Time-to-live for cached health status (default 5 minutes)
        """
        self.ttl = ttl_seconds
        
        # Use provided Redis client or create new one
        if redis_client:
            self.redis = redis_client
        else:
            try:
                # Use Redis DB 2 for metrics (same as metrics_cache)
                self.redis = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    db=2,
                    decode_responses=True
                )
                self.redis.ping()
                logger.info("Provider health cache connected to Redis DB 2")
            except Exception as e:
                logger.error(f"Failed to connect to Redis for health cache: {e}")
                # Fallback to in-memory if Redis unavailable
                self.redis = None
                self._fallback_cache = {}
                
    def validate_provider_config(self, provider: str, model: str, api_url: str, api_key: str = None) -> Tuple[bool, str]:
        """
        Validate provider configuration before health check.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Local providers (ollama) require api_url only
        if provider == 'ollama':
            if not api_url:
                return False, "misconfigured:missing_api_url"
            return True, None
            
        # Cloud providers require both api_url and api_key
        cloud_providers = ['openai', 'azure', 'gemini', 'anthropic']
        if provider in cloud_providers:
            if not api_url:
                return False, "misconfigured:missing_api_url"
            if not api_key:
                return False, "misconfigured:missing_api_key"
            return True, None
            
        # Unknown provider type - allow but warn
        logger.warning(f"Unknown provider type: {provider}")
        if not api_url:
            return False, "misconfigured:missing_api_url"
        return True, None
        
    def get_provider_health(self, provider: str, model: str) -> Optional[Dict]:
        """
        Get cached health status for a provider from Redis.
        
        Returns:
            Dict with health info if cached and valid, None if expired/missing
        """
        cache_key = f"provider_health:{provider}:{model}"
        
        if self.redis:
            try:
                data = self.redis.get(cache_key)
                if data:
                    health_data = json.loads(data)
                    logger.debug({
                        "event": "provider_health_cache_hit",
                        "provider": provider,
                        "model": model,
                        "status": health_data.get('status'),
                        "cached_at": health_data.get('checked_at')
                    })
                    return health_data
            except Exception as e:
                logger.error(f"Redis error getting health: {e}")
        else:
            # Fallback to in-memory cache
            if cache_key in self._fallback_cache:
                entry = self._fallback_cache[cache_key]
                if time.time() - entry['timestamp'] < self.ttl:
                    return entry['data']
                else:
                    del self._fallback_cache[cache_key]
                    
        return None
        
    def set_provider_health(self, provider: str, model: str, status: str, 
                           response_time_ms: int = None, error: str = None):
        """
        Cache provider health status in Redis.
        
        Args:
            status: 'healthy', 'unhealthy', or 'misconfigured'
            response_time_ms: Response time if healthy
            error: Error message if unhealthy/misconfigured
        """
        cache_key = f"provider_health:{provider}:{model}"
        
        health_data = {
            'status': status,
            'checked_at': datetime.now().isoformat(),
            'response_time_ms': response_time_ms,
            'error': error,
            'provider': provider,
            'model': model
        }
        
        if self.redis:
            try:
                self.redis.setex(
                    cache_key,
                    self.ttl,
                    json.dumps(health_data)
                )
            except Exception as e:
                logger.error(f"Redis error setting health: {e}")
                # Fall back to in-memory
                self._fallback_cache[cache_key] = {
                    'data': health_data,
                    'timestamp': time.time()
                }
        else:
            # Use in-memory cache
            self._fallback_cache[cache_key] = {
                'data': health_data,
                'timestamp': time.time()
            }
            
        logger.info({
            "event": "provider_health_cached",
            "provider": provider,
            "model": model,
            "status": status,
            "ttl_seconds": self.ttl,
            "error": error
        })
        
    def get_healthy_fallback_chain(self, original_chain: List[dict]) -> List[dict]:
        """
        Filter fallback chain to only include healthy providers.
        Validates configuration and performs health checks as needed.
        
        Args:
            original_chain: Original fallback chain from config
            
        Returns:
            List of healthy providers only
        """
        healthy_chain = []
        misconfigured_count = 0
        unhealthy_count = 0
        
        logger.info({
            "event": "get_healthy_fallback_chain_started",
            "original_count": len(original_chain),
            "first_3_entries": original_chain[:3] if original_chain else []
        })
        
        for entry in original_chain:
            provider = entry.get('provider')
            model = entry.get('model', entry.get('deployment_name', 'default'))
            api_url = entry.get('api_url')
            api_key = entry.get('api_key')
            
            # For multiple instances of same provider/model, use unique ID
            # Extract port from URL for Ollama instances or use ID if available
            instance_id = entry.get('id')
            if not instance_id and provider == 'ollama' and api_url:
                # Extract port from URL like "http://localhost:11434/..."
                import re
                port_match = re.search(r':(\d+)/', api_url)
                if port_match:
                    instance_id = f"{model}:{port_match.group(1)}"
                    
            # Use instance_id if available for unique cache key
            cache_model = instance_id if instance_id else model
            
            if not provider:
                continue
                
            # Step 1: Validate configuration
            is_valid, error_msg = self.validate_provider_config(provider, model, api_url, api_key)
            if not is_valid:
                misconfigured_count += 1
                self.set_provider_health(provider, cache_model, 'misconfigured', error=error_msg)
                logger.warning({
                    "event": "provider_misconfigured",
                    "provider": provider,
                    "model": cache_model,
                    "error": error_msg
                })
                continue
                
            # Step 2: Check cached health status
            cached_health = self.get_provider_health(provider, cache_model)
            
            # Debug logging
            logger.debug({
                "event": "checking_cached_health",
                "provider": provider,
                "model": model,
                "cache_model": cache_model,
                "api_url": api_url,
                "cached_health_found": cached_health is not None,
                "cached_status": cached_health.get('status') if cached_health else None
            })
            
            if cached_health:
                if cached_health['status'] == 'healthy':
                    healthy_chain.append(entry)
                elif cached_health['status'] == 'unhealthy':
                    unhealthy_count += 1
                    logger.debug({
                        "event": "skipping_unhealthy_provider",
                        "provider": provider,
                        "model": cache_model,
                        "error": cached_health.get('error'),
                        "cached": True
                    })
                # Skip misconfigured (already logged)
            else:
                # Step 3: No cache - perform actual health check
                from utils.llm_health_check import is_llm_available_with_fallback
                
                start_time = time.time()
                is_healthy, error_details = is_llm_available_with_fallback(
                    provider=provider,
                    health_check_url=api_url,
                    api_url=api_url,
                    model=model,
                    timeout=5
                )
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if is_healthy:
                    self.set_provider_health(provider, cache_model, 'healthy', 
                                            response_time_ms=response_time_ms)
                    healthy_chain.append(entry)
                else:
                    unhealthy_count += 1
                    error_msg = f"{error_details.get('error_type')}:{error_details.get('error_message')}"
                    self.set_provider_health(provider, cache_model, 'unhealthy', error=error_msg)
                    logger.info({
                        "event": "provider_health_check_failed",
                        "provider": provider,
                        "model": cache_model,
                        "error": error_msg
                    })
                    
        logger.info({
            "event": "healthy_chain_computed",
            "original_count": len(original_chain),
            "healthy_count": len(healthy_chain),
            "misconfigured_count": misconfigured_count,
            "unhealthy_count": unhealthy_count,
            "healthy_providers": [f"{e.get('provider')}:{e.get('model')}" for e in healthy_chain]
        })
        
        return healthy_chain
        
    def invalidate_provider(self, provider: str, model: str):
        """
        Invalidate cached health status for a provider.
        Useful when a provider fails during actual use.
        """
        cache_key = f"provider_health:{provider}:{model}"
        
        if self.redis:
            try:
                self.redis.delete(cache_key)
            except Exception as e:
                logger.error(f"Redis error invalidating health: {e}")
        elif cache_key in self._fallback_cache:
            del self._fallback_cache[cache_key]
                
        logger.info({
            "event": "provider_health_invalidated",
            "provider": provider,
            "model": model
        })
        
    def get_all_health_status(self) -> Dict[str, Dict]:
        """
        Get health status for all providers (for admin portal).
        
        Returns:
            Dict mapping provider:model to health data
        """
        all_status = {}
        
        if self.redis:
            try:
                # Get all provider health keys
                keys = self.redis.keys("provider_health:*")
                for key in keys:
                    data = self.redis.get(key)
                    if data:
                        health_data = json.loads(data)
                        # Extract provider:model from key
                        parts = key.split(":", 2)
                        if len(parts) == 3:
                            provider_model = f"{parts[1]}:{parts[2]}"
                            all_status[provider_model] = health_data
            except Exception as e:
                logger.error(f"Redis error getting all health: {e}")
        else:
            # Fallback to in-memory cache
            for key, value in self._fallback_cache.items():
                if key.startswith("provider_health:"):
                    if time.time() - value['timestamp'] < self.ttl:
                        parts = key.split(":", 2)
                        if len(parts) == 3:
                            provider_model = f"{parts[1]}:{parts[2]}"
                            all_status[provider_model] = value['data']
                            
        return all_status
        
    def clear_cache(self):
        """Clear all cached health statuses."""
        if self.redis:
            try:
                keys = self.redis.keys("provider_health:*")
                if keys:
                    self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} health cache entries from Redis")
            except Exception as e:
                logger.error(f"Redis error clearing health cache: {e}")
        else:
            self._fallback_cache.clear()
            
        logger.info({"event": "provider_health_cache_cleared"})

# Global singleton instance
try:
    # Try to use Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
    redis_client.ping()
    provider_health_cache = ProviderHealthCache(redis_client=redis_client, ttl_seconds=300)
except:
    # Fallback to in-memory if Redis unavailable
    provider_health_cache = ProviderHealthCache(redis_client=None, ttl_seconds=300)