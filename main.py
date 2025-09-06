"""
Wag-Tail AI Gateway - Open Source Edition
A lightweight, secure AI gateway with PII protection and content filtering
"""

import os
import json
import time
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local imports
from config_loader import load_config
from plugin_loader import load_plugins, get_user_edition
from database_loader import validate_api_key, init_database
from wag_tail_logger import get_logger
from response_loader import create_response
from header_model_selector import select_model_from_header

# Import LLM providers
from llm_providers.ollama import query_ollama
from llm_providers.gemini import query_gemini
from llm_providers.azure import query_azure

# Initialize logger
logger = get_logger(__name__)

# Load configuration
config = load_config()

# Global variables for plugins
plugins = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Wag-Tail AI Gateway - OSS Edition")
    
    # Initialize database
    init_database()
    
    # Load plugins
    global plugins
    plugins = load_plugins()
    logger.info(f"Loaded {len(plugins)} plugins for {get_user_edition()} edition")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Wag-Tail AI Gateway")

# Create FastAPI app
app = FastAPI(
    title="Wag-Tail AI Gateway - OSS Edition",
    description="Open Source AI Gateway with Security Features",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model"""
    messages: Optional[List[Dict[str, str]]] = None
    prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=32000)
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    """Chat response model"""
    response: Optional[str] = None
    error: Optional[str] = None
    flag: Optional[str] = "safe"
    reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    provider: Optional[str] = None

# Authentication dependency
async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Validate API key
    key_info = validate_api_key(x_api_key)
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return key_info

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Wag-Tail AI Gateway - OSS Edition",
        "version": "1.0.0",
        "edition": get_user_edition(),
        "plugins_loaded": len(plugins),
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "edition": get_user_edition(),
        "plugins": len(plugins)
    }

@app.post("/chat")
async def chat(
    request: ChatRequest,
    key_info: Dict[str, Any] = Depends(verify_api_key),
    x_llm_provider: Optional[str] = Header(None),
    x_llm_model: Optional[str] = Header(None)
):
    """Main chat endpoint"""
    start_time = time.time()
    
    try:
        # Extract prompt from request
        if request.messages:
            prompt = request.messages[-1].get("content", "")
        elif request.prompt:
            prompt = request.prompt
        else:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        # Select model and provider
        provider = x_llm_provider or config.get("llm", {}).get("provider", "ollama")
        model = x_llm_model or request.model or config.get("llm", {}).get("model", "mistral")
        
        # Create context for plugins
        context = {
            "request": request.dict(),
            "prompt": prompt,
            "api_key_info": key_info,
            "provider": provider,
            "model": model,
            "plugins": {}
        }
        
        # Run pre-request plugins
        for plugin in plugins:
            if hasattr(plugin, 'on_request'):
                try:
                    result = plugin.on_request(context)
                    if result:
                        # Plugin blocked the request
                        if isinstance(result, dict) and result.get("flag") == "blocked":
                            return JSONResponse(
                                status_code=200,
                                content={
                                    "response": result.get("response", {"error": "Content blocked"}),
                                    "flag": "blocked",
                                    "reason": result.get("reason", "Security policy violation"),
                                    "classified_type": result.get("classified_type"),
                                    "processing_time": time.time() - start_time
                                }
                            )
                except Exception as e:
                    logger.error(f"Plugin error in {plugin.__class__.__name__}: {e}")
        
        # Call LLM provider
        llm_response = None
        if provider == "ollama":
            llm_response = await query_ollama(
                prompt=prompt,
                model=model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider == "gemini":
            llm_response = await query_gemini(
                prompt=prompt,
                model=model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider == "azure":
            llm_response = await query_azure(
                prompt=prompt,
                model=model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider == "openai":
            # OpenAI support can be added here
            raise HTTPException(status_code=501, detail="OpenAI provider not implemented in OSS edition")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
        
        # Check if LLM call failed
        if not llm_response or "error" in llm_response:
            return JSONResponse(
                status_code=500,
                content={
                    "error": llm_response.get("error", "LLM provider error"),
                    "provider": provider,
                    "model": model
                }
            )
        
        # Update context with response
        context["response"] = llm_response
        
        # Run post-response plugins
        for plugin in plugins:
            if hasattr(plugin, 'on_response'):
                try:
                    result = plugin.on_response(context)
                    if result:
                        # Plugin modified or blocked the response
                        if isinstance(result, dict) and result.get("flag") == "blocked":
                            return JSONResponse(
                                status_code=200,
                                content={
                                    "response": {"error": "Response blocked"},
                                    "flag": "blocked",
                                    "reason": result.get("reason", "Output policy violation"),
                                    "processing_time": time.time() - start_time
                                }
                            )
                except Exception as e:
                    logger.error(f"Plugin error in {plugin.__class__.__name__}: {e}")
        
        # Return successful response
        return JSONResponse(
            status_code=200,
            content={
                "response": llm_response.get("response", llm_response.get("text", "")),
                "flag": "safe",
                "model": model,
                "provider": provider,
                "usage": llm_response.get("usage"),
                "processing_time": time.time() - start_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "processing_time": time.time() - start_time
            }
        )

@app.get("/plugins")
async def get_plugins():
    """Get loaded plugins information"""
    plugin_info = []
    for plugin in plugins:
        plugin_info.append({
            "name": plugin.__class__.__name__,
            "module": plugin.__class__.__module__,
            "has_on_request": hasattr(plugin, 'on_request'),
            "has_on_response": hasattr(plugin, 'on_response')
        })
    
    return {
        "edition": get_user_edition(),
        "total_plugins": len(plugins),
        "plugins": plugin_info
    }

@app.get("/config")
async def get_config(key_info: Dict[str, Any] = Depends(verify_api_key)):
    """Get current configuration (admin only)"""
    # Check if user is admin
    if key_info.get("organization") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Return sanitized config
    safe_config = {
        "edition": get_user_edition(),
        "llm": {
            "provider": config.get("llm", {}).get("provider"),
            "model": config.get("llm", {}).get("model")
        },
        "security": {
            "pii_detection": config.get("security", {}).get("enable_pii_detection", True),
            "code_detection": config.get("security", {}).get("enable_code_detection", True)
        },
        "plugins_loaded": len(plugins)
    }
    
    return safe_config

# Error handlers
@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found"}
    )

@app.exception_handler(500)
async def server_error(request: Request, exc: Exception):
    logger.error(f"Server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)