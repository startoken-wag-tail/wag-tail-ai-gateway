# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

import time
from wag_tail_logger import logger

# Import load balancer for multi-instance support
try:
    from utils.llm_load_balancer import get_load_balancer
    load_balancer = get_load_balancer()
except ImportError:
    load_balancer = None

def query(
    prompt: str,
    timeout: int,
    api_url: str = None,
    api_key: str = None,
    model: str = "mistral",
    plugins=None,
    max_tokens: int = None,
    stream: bool = False,
    request_id: str = None  # For session affinity in load balancing
) -> dict:
    """
    Query Mistral (Ollama) LLM with streaming response support and multi-instance load balancing.
    Uses config values first, then plugins, then fallback.
    """
    # Check if load balancer has multi-instance configuration for mistral
    instance_info = None
    if load_balancer:
        try:
            # Try to get an instance from the load balancer
            instance_url, instance_info = load_balancer.get_instance(
                'mistral', 
                {'session_id': request_id} if request_id else None
            )
            if instance_url:
                # Use the load-balanced URL
                url = instance_url
                logger.info({
                    "message": "Using load-balanced Mistral instance",
                    "instance": instance_info.name if instance_info else "single",
                    "url": url
                })
            else:
                # No instance available from load balancer, use supplied config
                url = api_url
        except Exception as e:
            logger.warning(f"Load balancer error, falling back to direct URL: {e}")
            url = api_url
    else:
        # 1. Use supplied config if present
        url = api_url
    
    key = api_key

    # 2. If missing, try plugin-based secret lookup
    if (not url or not key) and plugins is not None:
        for plugin in plugins:
            if hasattr(plugin, "get_secret"):
                if not url:
                    try:
                        v = plugin.get_secret("MISTRAL_API_URL")
                        if v: url = v
                    except Exception:
                        pass
                if not key:
                    try:
                        v = plugin.get_secret("MISTRAL_API_KEY")
                        if v: key = v
                    except Exception:
                        pass
            if url and key:
                break

    # 3. Fallback to hardcoded defaults (Ollama)
    if not url:
        logger.info({
            "message": "MISTRAL_API_URL fallback to default",
            "module": "mistral",
            "event": "mistral_api_url_fallback",
            "url": "http://localhost:11434/api/generate"
        })
        url = "http://localhost:11434/api/generate"  # fallback default
    if not key:
        logger.info({
            "message": "MISTRAL_API_KEY fallback to default",
            "module": "mistral",
            "event": "mistral_api_key_fallback"
        })
        key = ""

    # Build payload with Ollama parameters
    payload = {
        "model": model, 
        "prompt": prompt,
        "stream": stream  # Enable streaming for faster TTFT
    }
    
    # Add max_tokens as 'num_predict' for Ollama
    if max_tokens:
        payload["options"] = {
            "num_predict": max_tokens,  # Ollama uses 'num_predict' for max tokens
            "temperature": 0.7,
            "top_p": 0.9
        }
    
    headers = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    import requests
    import json

    request_success = False
    start_time = time.time()
    
    try:
        # Streaming request for Ollama!
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)
        resp.raise_for_status()
        response_text = ""
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
                response_text += chunk.get("response", "")
            except Exception as decode_err:
                logger.error({
                    "message": "Error decoding Ollama chunk",
                    "module": "mistral",
                    "event": "decode_error",
                    "error": str(decode_err),
                    "line": line
                })
        
        request_success = True  # Mark as successful if we got a response
        result = {"text": response_text}
        
        # Report success to load balancer
        if instance_info and load_balancer:
            latency_ms = (time.time() - start_time) * 1000
            strategy = load_balancer.strategies.get('mistral')
            if strategy:
                strategy.on_request_complete(instance_info, True, latency_ms)
                instance_info.active_connections = max(0, instance_info.active_connections - 1)
        
        return result
        
    except Exception as e:
        logger.error({
            "message": "Mistral query error",
            "module": "mistral",
            "event": "query_error",
            "error": str(e),
            "api_url": url
        })
        
        # Report failure to load balancer
        if instance_info and load_balancer:
            latency_ms = (time.time() - start_time) * 1000
            strategy = load_balancer.strategies.get('mistral')
            if strategy:
                strategy.on_request_complete(instance_info, False, latency_ms)
                instance_info.active_connections = max(0, instance_info.active_connections - 1)
        
        return {"error": str(e)}

# Example usage for dev/test:
# result = query("Say hello!", 10, api_url="http://localhost:11434/api/generate")
