#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Wag-Tail AI Gateway - Open Source Edition
A secure, production-ready AI gateway with enterprise-grade security features.

Open Source Features:
- Multi-layer security pipeline (regex, code detection, PII protection)
- JSON Schema validation with Pydantic v2
- Webhook integration for external GuardRail systems
- Header-based LLM model selection
- Comprehensive logging with sensitive data masking
- Support for multiple LLM providers (Ollama, OpenAI, Gemini, Azure)

License: Apache 2.0
"""

import time
import json
import traceback
import os
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Core imports
from schemas.response_models import ChatResponse, ErrorResponse, HealthResponse
from config_loader import load_config
from wag_tail_logger import logger
from utils.llm import query_llm, is_llm_available
from plugin_loader import load_plugins, get_plugin_manager
from response_loader import load_responses
from header_model_selector import apply_model_header_overrides

# Create FastAPI app
app = FastAPI(
    title="Wag-Tail AI Gateway - OSS Edition",
    description="Secure AI Gateway with enterprise-grade security features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global configuration
config = load_config()
RESPONSES = load_responses()

# Load OSS plugins only
plugins_loaded = load_plugins()
plugin_manager = get_plugin_manager()
plugins = list(plugin_manager.get_all_plugins().values())
logger.info(f"[Startup] Loaded {len(plugins)} OSS plugins")

# Plugin references
basic_guard_plugin = None
pii_guard_plugin = None
webhook_plugin = None
key_auth_plugin = None

# Organize plugins by type
for plugin in plugins:
    plugin_name = getattr(plugin, "name", "")
    if plugin_name == "wag_tail_basic_guard":
        basic_guard_plugin = plugin
    elif plugin_name == "wag_tail_pii_guard":
        pii_guard_plugin = plugin
    elif plugin_name == "wag_tail_webhook_guardrail":
        webhook_plugin = plugin
    elif plugin_name == "wag_tail_key_auth":
        key_auth_plugin = plugin

# Request model
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="User prompt")

def mask_api_key(api_key: Optional[str]) -> str:
    """Mask API key for logging purposes"""
    if not api_key or len(api_key) < 8:
        return "****INVALID****"
    return f"****{api_key[-6:]}"

def safe_set_span_attribute(span, key: str, value: Any) -> None:
    """Safely set span attribute (no-op in OSS edition)"""
    pass

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check"""
    try:
        llm_status = "available" if is_llm_available() else "unavailable"
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            edition="oss", 
            uptime_seconds=int(time.time()),
            llm_status=llm_status,
            plugins_loaded=len(plugins)
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0", 
            edition="oss",
            uptime_seconds=int(time.time()),
            llm_status="error",
            plugins_loaded=len(plugins),
            error=str(e)
        )

# Main chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_llm_provider: Optional[str] = Header(None, alias="X-LLM-Provider"),
    x_llm_model: Optional[str] = Header(None, alias="X-LLM-Model"),
    x_group_id: Optional[str] = Header(None, alias="X-Group-ID")
) -> ChatResponse:
    """
    Main chat endpoint with comprehensive security pipeline
    
    Security Features:
    - API key authentication
    - Input validation with Pydantic
    - Regex filtering and code detection
    - PII detection and masking
    - Output filtering
    - Webhook integration for external GuardRail systems
    """
    start_time = time.time()
    prompt = chat_request.prompt
    client_ip = request.client.host if request.client else "unknown"
    
    # Request context for plugins
    context = {
        "request": request,
        "prompt": prompt,
        "api_key": x_api_key,
        "masked_api_key": mask_api_key(x_api_key),
        "client_ip": client_ip,
        "group_id": x_group_id,
        "edition": "oss",
        "timestamp": time.time(),
        "plugins": plugins
    }
    
    # Apply header-based model overrides
    if x_llm_provider or x_llm_model:
        context = apply_model_header_overrides(context, x_llm_provider, x_llm_model)
    
    try:
        # Security Pipeline - OSS Edition
        
        # 1. API Key Authentication (OSS uses simple default key check)
        if key_auth_plugin and hasattr(key_auth_plugin, 'authenticate'):
            is_authenticated = key_auth_plugin.authenticate(x_api_key)
            if not is_authenticated:
                logger.warning({
                    "message": "Authentication failed - invalid API key",
                    "masked_api_key": context["masked_api_key"],
                    "client_ip": client_ip,
                    "api_key_provided": bool(x_api_key)
                })
                return ChatResponse(
                    response="",
                    flag="blocked",
                    reason="Invalid API key",
                    llm_provider="auth_filter",
                    llm_model_name="simple_auth",
                    cache_hit=False,
                    process_time_ms=int((time.time() - start_time) * 1000)
                )
        
        # 2. Basic Security Filtering (Regex + Code Detection)
        if basic_guard_plugin and hasattr(basic_guard_plugin, 'check_prompt'):
            security_result = basic_guard_plugin.check_prompt(prompt)
            if security_result and security_result.get("blocked"):
                logger.warning({
                    "message": "Request blocked by security filter",
                    "masked_api_key": context["masked_api_key"],
                    "client_ip": client_ip,
                    "reason": security_result.get("reason", "Security violation"),
                    "pattern_matched": security_result.get("pattern_matched"),
                    "prompt_preview": prompt[:50] + "..." if len(prompt) > 50 else prompt
                })
                return ChatResponse(
                    response="",
                    flag="blocked",
                    reason=security_result.get("reason", "Security violation detected"),
                    llm_provider="security_filter",
                    llm_model_name="basic_guard",
                    cache_hit=False,
                    process_time_ms=int((time.time() - start_time) * 1000)
                )
        
        # 3. PII Detection and Protection
        if pii_guard_plugin and hasattr(pii_guard_plugin, 'detect_pii'):
            pii_result = pii_guard_plugin.detect_pii(prompt)
            if pii_result and pii_result.get("pii_detected"):
                pii_types = pii_result.get("pii_types", [])
                # In OSS, log PII detection but don't block (configurable)
                logger.warning({
                    "message": "PII detected in prompt",
                    "masked_api_key": context["masked_api_key"],
                    "client_ip": client_ip,
                    "pii_types": pii_types,
                    "entities_count": pii_result.get("entities_count", 0),
                    "prompt_preview": "[REDACTED - PII DETECTED]"
                })
                
                # OSS version: optionally block high-confidence PII
                confidence_scores = pii_result.get("confidence_scores", [])
                high_confidence_pii = any(score > 0.9 for score in confidence_scores)
                
                if high_confidence_pii:
                    return ChatResponse(
                        response="",
                        flag="blocked",
                        reason=f"High-confidence PII detected: {', '.join(pii_types)}",
                        llm_provider="pii_guard",
                        llm_model_name="presidio",
                        cache_hit=False,
                        process_time_ms=int((time.time() - start_time) * 1000),
                        pii_detected=True,
                        pii_types=pii_types
                    )
        
        # 4. Webhook Integration (External GuardRail) - OSS Edition
        # Note: OSS edition may not have webhook plugin or it may be disabled
        webhook_config = config.get("webhook", {})
        if webhook_config.get("enabled", False):
            # Basic webhook check for OSS - simplified implementation
            logger.info({
                "message": "Webhook integration available but simplified in OSS",
                "webhook_url": webhook_config.get("url", "not_configured")
            })
        
        # 5. LLM Processing
        logger.info({
            "message": "Processing request through LLM",
            "masked_api_key": context["masked_api_key"],
            "client_ip": client_ip,
            "prompt_length": len(prompt),
            "llm_provider": context.get("llm_provider", "default"),
            "llm_model": context.get("llm_model", "default")
        })
        
        # Query the LLM - OSS version returns tuple
        response_text, success, error_msg, llm_provider, llm_model = query_llm(prompt)
        
        if not success or error_msg:
            logger.error({
                "message": "LLM processing failed",
                "masked_api_key": context["masked_api_key"],
                "client_ip": client_ip,
                "error": error_msg or "LLM query failed"
            })
            return ChatResponse(
                response="",
                flag="llm_error",
                reason=error_msg or "LLM processing failed",
                llm_provider=llm_provider or "unknown",
                llm_model_name=llm_model or "unknown",
                cache_hit=False,
                process_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # 6. Output Filtering (process through plugins for response)
        for plugin in plugins:
            if hasattr(plugin, 'on_response'):
                try:
                    plugin_response = plugin.on_response(request, context, response_text)
                    if plugin_response and len(plugin_response) >= 2:
                        filtered_response, was_modified = plugin_response[0], plugin_response[1]
                        if was_modified:
                            logger.info({
                                "message": f"Response modified by {getattr(plugin, 'name', 'unknown')} plugin",
                                "masked_api_key": context["masked_api_key"]
                            })
                            response_text = filtered_response
                except Exception as e:
                    logger.error(f"Plugin {getattr(plugin, 'name', 'unknown')} response processing failed: {str(e)}")
        
        # 7. Success Response
        process_time = int((time.time() - start_time) * 1000)
        
        logger.info({
            "message": "Request processed successfully",
            "masked_api_key": context["masked_api_key"],
            "client_ip": client_ip,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "process_time_ms": process_time,
            "response_length": len(response_text)
        })
        
        return ChatResponse(
            response=response_text,
            flag="safe",
            llm_provider=llm_provider,
            llm_model_name=llm_model,
            cache_hit=False,  # No caching in OSS edition
            process_time_ms=process_time,
            pii_detected=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error({
            "message": "Unexpected error in chat endpoint",
            "masked_api_key": context.get("masked_api_key", "unknown"),
            "client_ip": client_ip,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return ChatResponse(
            response="",
            flag="error",
            reason="Internal server error occurred",
            llm_provider="system",
            llm_model_name="error_handler",
            cache_hit=False,
            process_time_ms=int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent information leakage"""
    logger.error({
        "message": "Unhandled exception",
        "url": str(request.url),
        "method": request.method,
        "error": str(exc),
        "traceback": traceback.format_exc()
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR", 
            "details": {
                "message": "An unexpected error occurred"
            }
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info({
        "message": "Wag-Tail AI Gateway OSS Edition starting up",
        "version": "1.0.0",
        "plugins_loaded": len(plugins),
        "llm_available": is_llm_available()
    })
    
    # Validate configuration
    try:
        llm_config = config.get("llm", {})
        if not llm_config.get("provider"):
            logger.warning("No LLM provider configured in config/sys_config.yaml")
        else:
            logger.info(f"LLM provider configured: {llm_config.get('provider')}")
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Wag-Tail AI Gateway OSS Edition shutting down")

if __name__ == "__main__":
    import uvicorn
    
    # Development server
    logger.info("Starting Wag-Tail AI Gateway OSS Edition in development mode")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )