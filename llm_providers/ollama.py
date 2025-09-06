# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Ollama provider implementation for Wag-Tail AI Gateway
Supports local Ollama instances running on various ports
"""

import requests
import json
from wag_tail_logger import logger


def query(prompt, timeout=60, api_url=None, api_key=None, model="mistral:7b-instruct-q4_K_M", **kwargs):
    """
    Query Ollama API for LLM response using OpenAI-compatible endpoint
    
    Args:
        prompt: The user's prompt text
        timeout: Request timeout in seconds
        api_url: Full URL including endpoint (e.g., http://localhost:11434/v1/chat/completions)
        api_key: Not used for Ollama (local service)
        model: Model name (e.g., mistral:7b-instruct-q4_K_M)
        **kwargs: Additional parameters (max_tokens, stream, etc.)
    
    Returns:
        dict: {"text": response_text, "error": None} on success
              {"text": "", "error": error_message} on failure
    """
    try:
        if not api_url:
            logger.error("[Ollama] No API URL provided")
            return {"text": "", "error": "No API URL provided"}
        
        # Use the provided URL directly (should already include /v1/chat/completions)
        url = api_url
        
        # Build OpenAI-compatible request payload
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False  # Don't stream for simplicity in gateway context
        }
        
        # Add optional parameters if provided
        if "max_tokens" in kwargs and kwargs["max_tokens"]:
            payload["num_predict"] = kwargs["max_tokens"]  # Ollama uses num_predict
        
        if "temperature" in kwargs and kwargs["temperature"] is not None:
            payload["temperature"] = kwargs["temperature"]
        
        if "top_p" in kwargs and kwargs["top_p"] is not None:
            payload["top_p"] = kwargs["top_p"]
        
        # Ollama doesn't need authentication (local service)
        headers = {"Content-Type": "application/json"}
        
        logger.debug({
            "message": "[Ollama] Sending request",
            "url": url,
            "model": model,
            "timeout": timeout
        })
        
        # Make the request
        response = requests.post(
            url, 
            json=payload, 
            headers=headers, 
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            # Parse Ollama response format
            response_text = ""
            if "message" in data:
                # Ollama native format
                response_text = data["message"].get("content", "")
            elif "choices" in data and len(data["choices"]) > 0:
                # OpenAI-compatible format (in case Ollama updates)
                response_text = data["choices"][0].get("message", {}).get("content", "")
            
            # Log success
            logger.info({
                "message": "[Ollama] Successfully got response",
                "model": model,
                "response_length": len(response_text),
                "api_url": api_url
            })
            
            return {"text": response_text, "error": None}
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error({
                "message": "[Ollama] Request failed",
                "status_code": response.status_code,
                "error": error_msg,
                "api_url": api_url,
                "model": model
            })
            return {"text": "", "error": error_msg}
            
    except requests.exceptions.Timeout:
        error_msg = f"Request timed out after {timeout}s"
        logger.error({
            "message": "[Ollama] Timeout",
            "timeout": timeout,
            "api_url": api_url,
            "model": model
        })
        return {"text": "", "error": error_msg}
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection failed: {str(e)}"
        logger.error({
            "message": "[Ollama] Connection error",
            "error": str(e),
            "api_url": api_url,
            "model": model
        })
        return {"text": "", "error": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error({
            "message": "[Ollama] Unexpected error",
            "error": str(e),
            "api_url": api_url,
            "model": model
        })
        return {"text": "", "error": error_msg}


def health_check(api_url, model="mistral:7b-instruct-q4_K_M", timeout=5):
    """
    Check if Ollama instance is healthy
    
    Args:
        api_url: Base URL for Ollama instance
        model: Model to check
        timeout: Health check timeout
    
    Returns:
        bool: True if healthy, False otherwise
    """
    try:
        # Use the /api/tags endpoint for a lightweight health check
        url = f"{api_url}/api/tags"
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            # Check if the requested model is available
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if model in model_names:
                logger.debug(f"[Ollama] Health check passed for {api_url}, model {model} available")
                return True
            else:
                logger.warning(f"[Ollama] Model {model} not found in {api_url}")
                return False
        else:
            logger.warning(f"[Ollama] Health check failed for {api_url}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        logger.warning(f"[Ollama] Health check failed for {api_url}: {e}")
        return False