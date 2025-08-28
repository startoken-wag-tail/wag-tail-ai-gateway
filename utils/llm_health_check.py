"""
Enhanced health check with simple fallback: health_check_url → api_url
No hardcoded URLs - everything from YAML configuration
"""

import requests
from datetime import datetime
from wag_tail_logger import logger


def is_llm_available_with_fallback(provider, health_check_url=None, api_url=None, model=None, timeout=5):
    """
    Health check with simple fallback logic.
    Tries health_check_url first, falls back to api_url if needed.
    
    Args:
        provider: LLM provider name
        health_check_url: Primary health check endpoint from YAML
        api_url: Fallback API endpoint from YAML
        model: Model name for context
        timeout: Request timeout in seconds
        
    Returns:
        tuple: (bool, dict) - (is_healthy, error_details)
    """
    
    # Build list of URLs to try
    urls_to_try = []
    if health_check_url and health_check_url.strip():
        urls_to_try.append(("health_check_url", health_check_url))
    if api_url and api_url.strip() and api_url != health_check_url:
        urls_to_try.append(("api_url", api_url))
    
    if not urls_to_try:
        error_details = {
            "error_type": "configuration",
            "error_message": "No URLs configured",
            "admin_action": "Configure health_check_url or api_url in llm_routing.yaml"
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
    
    # Try each URL in sequence
    last_error = None
    for url_type, url in urls_to_try:
        logger.debug({
            "event": "health_check_attempt",
            "provider": provider,
            "model": model,
            "url_type": url_type,
            "url": url
        })
        
        try:
            # For chat completions endpoints, use POST with minimal payload
            if '/chat/completions' in url or '/v1/chat/completions' in url:
                # Minimal valid request for chat endpoint
                test_payload = {
                    "model": model or "test",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                    "temperature": 0
                }
                response = requests.post(url, json=test_payload, timeout=timeout)
            else:
                # Try HEAD request first (lightweight)
                response = requests.head(url, timeout=timeout)
                
                # If HEAD not supported, try GET
                if response.status_code in [404, 405]:
                    response = requests.get(url, timeout=timeout)
            
            # Check response status
            if response.status_code == 200:
                logger.info({
                    "event": "llm_health_check_success",
                    "provider": provider,
                    "model": model,
                    "url_type": url_type,
                    "url": url,
                    "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat()
                })
                return True, {
                    "error_type": "none",
                    "error_message": None,
                    "admin_action": None,
                    "used_url": url,
                    "url_type": url_type
                }
            
            # 401/403 means service is up but needs auth - consider healthy
            elif response.status_code in [401, 403]:
                logger.info({
                    "event": "llm_health_check_auth_required",
                    "provider": provider,
                    "model": model,
                    "url_type": url_type,
                    "url": url,
                    "status_code": response.status_code
                })
                return True, {
                    "error_type": "auth_required",
                    "error_message": f"Service responsive (HTTP {response.status_code})",
                    "admin_action": "Check API key if needed",
                    "used_url": url,
                    "url_type": url_type
                }
            
            # Other status codes - try next URL
            else:
                last_error = {
                    "error_type": "http_error",
                    "error_message": f"HTTP {response.status_code}: {response.reason}",
                    "admin_action": "Check provider service status",
                    "failed_url": url,
                    "url_type": url_type
                }
                logger.debug({
                    "event": "health_check_http_error",
                    "provider": provider,
                    "url_type": url_type,
                    "url": url,
                    "status_code": response.status_code,
                    "trying_next": url != urls_to_try[-1][1]
                })
                continue
                
        except requests.exceptions.Timeout:
            last_error = {
                "error_type": "timeout",
                "error_message": f"Timeout after {timeout}s",
                "admin_action": "Check network/service",
                "failed_url": url,
                "url_type": url_type
            }
            logger.debug({
                "event": "health_check_timeout",
                "provider": provider,
                "url_type": url_type,
                "url": url,
                "trying_next": url != urls_to_try[-1][1]
            })
            continue
            
        except requests.exceptions.ConnectionError as e:
            last_error = {
                "error_type": "connection",
                "error_message": f"Connection failed: {str(e)}",
                "admin_action": "Check network connectivity",
                "failed_url": url,
                "url_type": url_type
            }
            logger.debug({
                "event": "health_check_connection_error",
                "provider": provider,
                "url_type": url_type,
                "url": url,
                "trying_next": url != urls_to_try[-1][1]
            })
            continue
            
        except Exception as e:
            last_error = {
                "error_type": "exception",
                "error_message": str(e),
                "admin_action": "Review logs",
                "failed_url": url,
                "url_type": url_type
            }
            logger.debug({
                "event": "health_check_exception",
                "provider": provider,
                "url_type": url_type,
                "url": url,
                "error": str(e),
                "trying_next": url != urls_to_try[-1][1]
            })
            continue
    
    # All URLs failed
    logger.error({
        "event": "llm_health_check_all_failed",
        "provider": provider,
        "model": model,
        "urls_tried": len(urls_to_try),
        "severity": "critical",
        "timestamp": datetime.now().isoformat(),
        **(last_error or {})
    })
    
    return False, last_error or {
        "error_type": "all_failed",
        "error_message": "All health check attempts failed",
        "admin_action": "Check both health_check_url and api_url in llm_routing.yaml"
    }