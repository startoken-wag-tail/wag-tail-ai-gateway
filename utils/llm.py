# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

import requests
from datetime import datetime
import threading
import time
from wag_tail_logger import logger
from config_loader import load_config

# Load global config once
config = load_config()

# Global LLM health status cache (system variable storage)
llm_health_cache = {
    "last_updated": None,
    "overall_status": "unknown",
    "providers": {},
    "summary": {"total_providers": 0, "healthy_providers": 0, "unhealthy_providers": 0}
}

# Background health checker control
_health_checker_thread = None
_health_checker_running = False

# Built-in provider request defaults
DEFAULT_PROVIDER_CONFIG = {
    "mistral": {
        "payload": {"model": "{model}", "prompt": "{prompt}"},
        "headers": {"Authorization": "Bearer {api_key}"},
    },
    "openai": {
        "payload": {
            "model": "{model}",
            "messages": [{"role": "user", "content": "{prompt}"}]
        },
        "headers": {"Authorization": "Bearer {api_key}"},
    },
    "gemini": {
        "payload": {"contents": [{"parts": [{"text": "{prompt}"}]}]},
        "headers": {"Authorization": "Bearer {api_key}"},
    },
    "claude": {
        "payload": {"model": "{model}", "prompt": "{prompt}"},
        "headers": {"Authorization": "Bearer {api_key}"},
    }
}


def is_llm_available(provider, api_url=None, model=None, timeout=5):
    """
    Enhanced health check with detailed error logging for system admins.
    
    Args:
        provider: LLM provider name (openai, azure, mistral, etc.)
        api_url: API endpoint URL
        model: Model name for context
        timeout: Request timeout in seconds
        
    Returns:
        tuple: (bool, dict) - (is_healthy, error_details)
               error_details contains error_type, error_message, admin_action
    """
    if not api_url:
        error_details = {
            "error_type": "configuration",
            "error_message": "No API URL configured",
            "admin_action": "Configure api_url in llm_routing.yaml"
        }
        logger.warning({
            "event": "llm_health_check_failed",
            "provider": provider,
            "model": model,
            "severity": "warning",
            "timestamp": datetime.now().isoformat(),
            **error_details
        })
        return False, error_details
    
    try:
        # Use HEAD request first (lighter than GET)
        response = requests.head(api_url, timeout=timeout)
        
        # If HEAD not supported, try GET
        # Some APIs return 404 instead of 405 for unsupported HEAD requests
        if response.status_code in [404, 405]:  # Method Not Allowed or Not Found for HEAD
            response = requests.get(api_url, timeout=timeout)
        
        if response.status_code == 200:
            logger.info({
                "event": "llm_health_check_success",
                "provider": provider,
                "model": model,
                "api_url": api_url,
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            })
            return True, {"error_type": "none", "error_message": None, "admin_action": None}
        elif response.status_code == 401:
            error_details = {
                "error_type": "authentication",
                "error_message": f"Authentication failed (HTTP {response.status_code})",
                "admin_action": "Check API key configuration"
            }
            logger.error({
                "event": "llm_health_check_failed",
                "provider": provider,
                "model": model,
                "api_url": api_url,
                "severity": "critical",
                "timestamp": datetime.now().isoformat(),
                **error_details
            })
            return False, error_details
        elif response.status_code == 429:
            error_details = {
                "error_type": "rate_limit",
                "error_message": f"Rate limited (HTTP {response.status_code})",
                "admin_action": "Provider temporarily rate limited, will retry"
            }
            logger.warning({
                "event": "llm_health_check_failed",
                "provider": provider,
                "model": model,
                "api_url": api_url,
                "severity": "warning",
                "timestamp": datetime.now().isoformat(),
                **error_details
            })
            return False, error_details
        else:
            error_details = {
                "error_type": "http_error",
                "error_message": f"HTTP {response.status_code}: {response.reason}",
                "admin_action": "Check provider service status and API configuration"
            }
            logger.error({
                "event": "llm_health_check_failed",
                "provider": provider,
                "model": model,
                "api_url": api_url,
                "severity": "critical",
                "timestamp": datetime.now().isoformat(),
                **error_details
            })
            return False, error_details
            
    except requests.exceptions.Timeout:
        error_details = {
            "error_type": "timeout",
            "error_message": f"Connection timeout after {timeout}s",
            "admin_action": "Check network connectivity and provider service status"
        }
        logger.error({
            "event": "llm_health_check_failed",
            "provider": provider,
            "model": model,
            "api_url": api_url,
            "severity": "critical",
            "timestamp": datetime.now().isoformat(),
            **error_details
        })
        # Track timeout for monitoring
        try:
            from utils.timeout_tracker import timeout_tracker
            timeout_tracker.record_timeout(
                provider=provider,
                model=model or "unknown",
                timeout_seconds=timeout,
                error_details="Health check timeout"
            )
        except:
            pass
        return False, error_details
    except requests.exceptions.ConnectionError as e:
        error_details = {
            "error_type": "connection",
            "error_message": f"Network connection failed: {str(e)}",
            "admin_action": "Check network connectivity and DNS resolution"
        }
        logger.error({
            "event": "llm_health_check_failed",
            "provider": provider,
            "model": model,
            "api_url": api_url,
            "severity": "critical",
            "timestamp": datetime.now().isoformat(),
            **error_details
        })
        return False, error_details
    except requests.exceptions.SSLError as e:
        error_details = {
            "error_type": "ssl",
            "error_message": f"SSL/TLS error: {str(e)}",
            "admin_action": "Check SSL certificate validity and TLS configuration"
        }
        logger.error({
            "event": "llm_health_check_failed",
            "provider": provider,
            "model": model,
            "api_url": api_url,
            "severity": "critical",
            "timestamp": datetime.now().isoformat(),
            **error_details
        })
        return False, error_details
    except Exception as e:
        error_details = {
            "error_type": "unknown",
            "error_message": f"Unexpected error: {str(e)}",
            "admin_action": "Review logs and contact support if issue persists"
        }
        logger.error({
            "event": "llm_health_check_failed",
            "provider": provider,
            "model": model,
            "api_url": api_url,
            "severity": "critical",
            "timestamp": datetime.now().isoformat(),
            **error_details
        })
        return False, error_details


def check_all_llm_providers_health():
    """
    Check health status of all configured LLM providers.
    Returns comprehensive status for admin monitoring and portal display.
    
    Returns:
        dict: {
            "overall_status": "healthy|degraded|critical",
            "providers": {
                "provider_name": {
                    "status": "healthy|unhealthy",
                    "model": "model_name", 
                    "response_time_ms": 123,
                    "error_type": "timeout|auth|connection|none",
                    "last_checked": "2025-01-16T10:30:15Z"
                }
            },
            "summary": {
                "total_providers": 5,
                "healthy_providers": 3,
                "unhealthy_providers": 2
            }
        }
    """
    from config_loader import load_config
    from utils.provider_health_cache import ProviderHealthCache
    
    # Initialize health cache to store results in Redis
    health_cache = ProviderHealthCache()
    
    # Load LLM routing configuration using the resolver to properly expand references
    try:
        from utils.llm_routing_resolver import load_and_resolve_routing_config
        routing_config = load_and_resolve_routing_config('config/llm_routing.yaml')
    except Exception as e:
        logger.error({
            "event": "llm_health_check_config_failed",
            "error_message": f"Failed to load llm_routing.yaml: {str(e)}",
            "severity": "critical",
            "timestamp": datetime.now().isoformat(),
            "admin_action": "Check llm_routing.yaml file exists and is valid YAML"
        })
        return {
            "overall_status": "critical",
            "providers": {},
            "summary": {"total_providers": 0, "healthy_providers": 0, "unhealthy_providers": 0},
            "error": "Configuration file not accessible"
        }
    
    fallback_chain = routing_config.get('fallback_chain', [])
    if not fallback_chain:
        logger.warning({
            "event": "llm_health_check_no_providers",
            "error_message": "No providers configured in fallback_chain",
            "severity": "warning",
            "timestamp": datetime.now().isoformat(),
            "admin_action": "Configure providers in llm_routing.yaml"
        })
        return {
            "overall_status": "critical",
            "providers": {},
            "summary": {"total_providers": 0, "healthy_providers": 0, "unhealthy_providers": 0},
            "error": "No providers configured"
        }
    
    providers_status = {}
    healthy_count = 0
    total_count = len(fallback_chain)
    
    logger.info({
        "event": "llm_health_check_started", 
        "total_providers": total_count,
        "timestamp": datetime.now().isoformat()
    })
    
    for idx, entry in enumerate(fallback_chain):
        provider = entry.get('provider')
        model = entry.get('model', entry.get('deployment_name', 'default'))
        api_url = entry.get('api_url')
        
        if not provider:
            continue
        
        # Get API key before checking
        api_key = entry.get('api_key', '')
        
        # Create unique provider key for each provider/model combination
        provider_key = f"{provider}_{model}" if model != 'default' else f"{provider}_{idx}"
        
        # For cache keys: Ollama needs instance-specific keys (with port), others use plain model
        cache_model = model  # Default to plain model name
        if provider == 'ollama' and api_url:
            # Extract port from URL for Ollama instances to create instance-specific cache key
            import re
            port_match = re.search(r':(\d+)/', api_url)
            if port_match:
                cache_model = f"{model}:{port_match.group(1)}"
            
        # Check for missing API key but still attempt connectivity check
        # Ollama is a local provider and doesn't require an API key
        missing_api_key = (not api_key or api_key.strip() == '' or api_key.startswith('your-') or api_key == 'xxx') and provider != 'ollama'
        
        if missing_api_key:
            # Still check connectivity even without API key to provide better diagnostics
            # Try a basic connectivity check without authentication
            if api_url and api_url.strip() != '':
                try:
                    import socket
                    from urllib.parse import urlparse
                    parsed = urlparse(api_url)
                    host = parsed.hostname or 'localhost'
                    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                    
                    # Quick socket check for connectivity
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    if result == 0:
                        # Service is reachable but API key is missing
                        error_details = {
                            "error_type": "missing_api_key",
                            "error_message": f"API key not configured for {provider} ({model})",
                            "admin_action": f"Service is reachable at {host}:{port}. Set valid API key in llm_routing.yaml for {provider}"
                        }
                    else:
                        # Service is not reachable AND API key is missing
                        error_details = {
                            "error_type": "missing_api_key_and_connection",
                            "error_message": f"API key not configured AND service unreachable for {provider} ({model})",
                            "admin_action": f"1) Check if service at {host}:{port} is running. 2) Set valid API key in llm_routing.yaml for {provider}"
                        }
                except Exception as e:
                    # Connectivity check failed
                    error_details = {
                        "error_type": "missing_api_key",
                        "error_message": f"API key not configured for {provider} ({model})",
                        "admin_action": f"Set valid API key in llm_routing.yaml for {provider}. Note: Could not verify service connectivity."
                    }
            else:
                error_details = {
                    "error_type": "missing_api_key",
                    "error_message": f"API key not configured for {provider} ({model})",
                    "admin_action": f"Set valid API key in llm_routing.yaml for {provider}"
                }
                
            providers_status[provider_key] = {
                "status": "unhealthy",
                "model": model,
                "provider": provider,
                "api_url": api_url,
                "response_time_ms": 0,
                "last_checked": datetime.now().isoformat(),
                "error_type": error_details.get("error_type", "none"),
                "error_message": error_details.get("error_message"),
                "admin_action": error_details.get("admin_action")
            }
            
            # Store misconfigured status in Redis cache
            health_cache.set_provider_health(
                provider=provider,
                model=cache_model,  # Use cache_model for instance-specific key
                status="misconfigured",
                response_time_ms=None,
                error=error_details.get("error_message")
            )
            
            continue
        
        # Check for missing API URL
        if not api_url or api_url.strip() == '':
            error_details = {
                "error_type": "missing_api_url",
                "error_message": f"API URL not configured for {provider} ({model})",
                "admin_action": f"Set valid API URL in llm_routing.yaml for {provider}"
            }
            providers_status[provider_key] = {
                "status": "unhealthy",
                "model": model,
                "provider": provider,
                "api_url": api_url,
                "response_time_ms": 0,
                "last_checked": datetime.now().isoformat(),
                "error_type": error_details.get("error_type", "none"),
                "error_message": error_details.get("error_message"),
                "admin_action": error_details.get("admin_action")
            }
            
            # Store misconfigured status in Redis cache
            health_cache.set_provider_health(
                provider=provider,
                model=cache_model,  # Use cache_model for instance-specific key
                status="misconfigured",
                response_time_ms=None,
                error=error_details.get("error_message")
            )
            
            continue
        
        # Get URLs from YAML configuration (source of truth)
        health_check_url = entry.get('health_check_url')
        
        # Import the new health check function with fallback logic
        from utils.llm_health_check import is_llm_available_with_fallback
        
        start_time = datetime.now()
        # Use new health check that tries health_check_url first, then api_url
        is_healthy, error_details = is_llm_available_with_fallback(
            provider=provider,
            health_check_url=health_check_url,
            api_url=api_url,
            model=model
        )
        check_duration = (datetime.now() - start_time).total_seconds() * 1000
        
        providers_status[provider_key] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "model": model,
            "provider": provider,
            "api_url": api_url,
            "response_time_ms": int(check_duration),
            "last_checked": datetime.now().isoformat(),
            "error_type": error_details.get("error_type", "none"),
            "error_message": error_details.get("error_message"),
            "admin_action": error_details.get("admin_action")
        }
        
        # Store health status in Redis cache
        health_cache.set_provider_health(
            provider=provider,
            model=cache_model,  # Use cache_model for instance-specific key
            status="healthy" if is_healthy else "unhealthy",
            response_time_ms=int(check_duration) if is_healthy else None,
            error=error_details.get("error_message") if not is_healthy else None
        )
        
        if is_healthy:
            healthy_count += 1
    
    # Determine overall system health
    if healthy_count == 0:
        overall_status = "critical"
        severity = "critical"
        admin_message = "ALL LLM providers are down - System unusable"
    elif healthy_count < total_count // 2:
        overall_status = "degraded" 
        severity = "warning"
        admin_message = f"Only {healthy_count}/{total_count} providers healthy - Degraded service"
    else:
        overall_status = "healthy"
        severity = "info"
        admin_message = f"{healthy_count}/{total_count} providers healthy - System operational"
    
    # Log overall system status
    getattr(logger, severity)({
        "event": "llm_health_check_completed",
        "overall_status": overall_status,
        "healthy_providers": healthy_count,
        "total_providers": total_count,
        "message": admin_message,
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "overall_status": overall_status,
        "providers": providers_status,
        "summary": {
            "total_providers": total_count,
            "healthy_providers": healthy_count,
            "unhealthy_providers": total_count - healthy_count
        }
    }


def _background_health_checker():
    """
    Background thread that updates LLM health cache every 60 seconds.
    Runs continuously while the application is running.
    """
    global llm_health_cache, _health_checker_running
    
    logger.info({"message": "LLM health background checker started", "interval_seconds": 60})
    
    while _health_checker_running:
        try:
            # Update the global cache with fresh health data
            health_status = check_all_llm_providers_health()
            health_status["last_updated"] = datetime.now().isoformat()
            
            llm_health_cache.update(health_status)
            
            logger.debug({
                "message": "LLM health cache updated",
                "overall_status": health_status["overall_status"],
                "healthy_providers": health_status["summary"]["healthy_providers"],
                "total_providers": health_status["summary"]["total_providers"]
            })
            
        except Exception as e:
            logger.error({
                "message": "LLM health background check failed",
                "error": str(e)
            })
        
        # Wait 60 seconds before next check
        time.sleep(60)
    
    logger.info({"message": "LLM health background checker stopped"})


def start_llm_health_monitoring():
    """
    Start the background LLM health monitoring thread.
    Call this during application startup.
    """
    global _health_checker_thread, _health_checker_running
    
    if _health_checker_running:
        logger.warning({"message": "LLM health monitoring already running"})
        return
    
    _health_checker_running = True
    _health_checker_thread = threading.Thread(target=_background_health_checker, daemon=True)
    _health_checker_thread.start()
    
    logger.info({"message": "LLM health monitoring started"})


def stop_llm_health_monitoring():
    """
    Stop the background LLM health monitoring thread.
    Call this during application shutdown.
    """
    global _health_checker_running
    
    _health_checker_running = False
    logger.info({"message": "LLM health monitoring stopped"})


def get_cached_llm_health():
    """
    Get cached LLM health status from system variable.
    Fast retrieval for admin API and portal display.
    
    Returns:
        dict: Cached health status or performs initial check if cache empty
    """
    global llm_health_cache
    
    # If cache is empty or very old, perform immediate check
    if (llm_health_cache["last_updated"] is None or 
        llm_health_cache["overall_status"] == "unknown"):
        logger.info({"message": "LLM health cache empty, performing initial check"})
        health_status = check_all_llm_providers_health()
        health_status["last_updated"] = datetime.now().isoformat()
        llm_health_cache.update(health_status)
    
    return llm_health_cache.copy()


def query_llm(prompt, fallback_chain, skip_health_check=False):
    """
    Executes an LLM query using the provided fallback_chain.
    NO HEALTH CHECKS during prompt processing - relies on fallback chain for resilience.
    fallback_chain: List[dict] → [{"provider": "...", "model": "..."}]
    skip_health_check: bool → Deprecated parameter, kept for compatibility

    Returns:
        dict: Raw JSON from first successful provider
        None: if all providers fail
    """
    if not fallback_chain:
        logger.error("[LLM] No fallback_chain provided to query_llm()")
        return None

    # NO HEALTH CHECKS - Just use the full fallback chain
    # The fallback mechanism naturally handles unhealthy providers
    # Health monitoring runs separately in background for alerting/dashboard
    
    logger.debug({
        "event": "using_fallback_chain",
        "message": "Processing without health checks - relying on fallback chain",
        "provider_count": len(fallback_chain)
    })

    # Load optional provider overrides from config
    overrides = config.get("providers", {})

    for entry in fallback_chain:  # Use full fallback_chain, no filtering
        provider = entry.get("provider")
        model = entry.get("model")

        if not provider or not model:
            logger.warning("[LLM] Skipping invalid fallback entry")
            continue

        # Resolve API URL & key - prioritize routing config, then fallback to global config
        api_url = entry.get("api_url") or config.get(provider.lower(), {}).get("api_url") or config.get("llm", {}).get("api_url")
        api_key = entry.get("api_key") or config.get(provider.lower(), {}).get("api_key") or config.get("llm", {}).get("api_key")
        # Use timeout from config, default to 30s for better reliability
        timeout = entry.get("timeout", 30)  # Increased from 10 to avoid premature timeouts

        # Skip health check - already filtered by healthy_chain
        # This saves time by not checking health again

        logger.info(f"[LLM] Sending prompt to provider={provider}, model={model}")

        try:
            # Route to provider-specific implementations first
            if provider.lower() == "ollama":
                from llm_providers import ollama
                # Extract optional parameters from entry
                max_tokens = entry.get("max_tokens", None)
                temperature = entry.get("temperature", None)
                top_p = entry.get("top_p", None)
                
                result = ollama.query(
                    prompt, timeout, api_url, api_key, model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p
                )
                if result and not result.get("error"):
                    response_text = result.get("text", "")
                    # Add metadata for tracking
                    class LLMResponse:
                        def __init__(self, text, provider, model):
                            self.text = text
                            self.provider = provider
                            self.model = model
                        def __str__(self):
                            return self.text
                    response_obj = LLMResponse(response_text, provider, model)
                    return response_obj
                else:
                    logger.warning(f"[LLM] Ollama provider failed: {result.get('error', 'Unknown error')}")
                    
            elif provider.lower() == "mistral":
                from llm_providers import mistral
                # Extract max_tokens and stream settings from route config
                max_tokens = entry.get("max_tokens", None)
                stream = entry.get("stream", True)  # Default to streaming for faster TTFT
                
                result = mistral.query(
                    prompt, timeout, api_url, api_key, model,
                    max_tokens=max_tokens, stream=stream
                )
                if result and not result.get("error"):
                    response_obj = result.get("text", "")
                    # Add metadata for tracking
                    if hasattr(response_obj, '__dict__'):
                        response_obj.provider = provider
                        response_obj.model = model
                    else:
                        # Create a wrapper object with metadata
                        class LLMResponse:
                            def __init__(self, text, provider, model):
                                self.text = text
                                self.provider = provider
                                self.model = model
                            def __str__(self):
                                return self.text
                        response_obj = LLMResponse(result.get("text", ""), provider, model)
                    return response_obj
                
            elif provider.lower() == "openai":
                from llm_providers import openai
                result = openai.query(prompt, timeout, api_url, api_key)
                if result and not result.get("error"):
                    return result.get("text", "")
                
            elif provider.lower() == "gemini":
                from llm_providers import gemini
                result = gemini.query(prompt, timeout, api_key, model)  # Gemini doesn't use api_url
                if result and not result.get("error"):
                    response_obj = result.get("text", "")
                    # Add metadata for tracking
                    if hasattr(response_obj, '__dict__'):
                        response_obj.provider = provider
                        response_obj.model = model
                    else:
                        # Create a wrapper object with metadata
                        class LLMResponse:
                            def __init__(self, text, provider, model):
                                self.text = text
                                self.provider = provider
                                self.model = model
                            def __str__(self):
                                return self.text
                        response_obj = LLMResponse(result.get("text", ""), provider, model)
                    return response_obj
            
            elif provider.lower() == "azure":
                from llm_providers import azure
                # Azure uses deployment_name instead of model
                deployment_name = entry.get("deployment_name", model)
                api_version = entry.get("api_version", "2024-02-01")
                result = azure.query(prompt, timeout, api_url, api_key, model, 
                                   deployment_name=deployment_name, 
                                   api_version=api_version)
                if result and not result.get("error"):
                    response_obj = result.get("text", "")
                    # Add metadata for tracking
                    if hasattr(response_obj, '__dict__'):
                        response_obj.provider = "azure"
                        response_obj.model = deployment_name
                    else:
                        # Create a wrapper object with metadata
                        class LLMResponse:
                            def __init__(self, text, provider, model):
                                self.text = text
                                self.provider = provider
                                self.model = model
                            def __str__(self):
                                return self.text
                        response_obj = LLMResponse(result.get("text", ""), "azure", deployment_name)
                    return response_obj
            
            
            else:
                # Generic fallback for unknown providers - check if we have config
                provider_conf = {**DEFAULT_PROVIDER_CONFIG.get(provider.lower(), {}), **overrides.get(provider.lower(), {})}
                
                if not provider_conf:
                    logger.error(f"[LLM] Provider '{provider}' not recognized and no override found — skipping.")
                    continue
                    
                payload = _substitute(provider_conf.get("payload", {}), model, prompt, api_key)
                headers = _substitute(provider_conf.get("headers", {}), model, prompt, api_key)
                response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response.json()
                logger.error(f"[LLM] {provider} returned {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"[LLM] Error calling {provider}: {e}, trying next in fallback chain")
            # Continue to next provider in fallback chain
            # NO CACHE INVALIDATION - Let background health monitor handle status updates

    logger.error("[LLM] All providers in fallback_chain failed or unavailable.")
    return None


def _substitute(template, model, prompt, api_key):
    """
    Recursively substitute placeholders in payload/header templates.
    """
    if isinstance(template, dict):
        return {k: _substitute(v, model, prompt, api_key) for k, v in template.items()}
    elif isinstance(template, list):
        return [_substitute(i, model, prompt, api_key) for i in template]
    elif isinstance(template, str):
        return template.format(model=model, prompt=prompt, api_key=api_key or "")
    return template
