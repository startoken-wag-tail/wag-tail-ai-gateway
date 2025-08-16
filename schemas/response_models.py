# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Response models for Wag-Tail AI Gateway OSS Edition
Pydantic v2 models for API request/response validation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal, Dict, Any, Union
from datetime import datetime

class ChatResponse(BaseModel):
    """Standard chat response model with comprehensive validation"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": "The answer is 42.",
                "flag": "safe",
                "llm_provider": "ollama",
                "llm_model_name": "mistral",
                "cache_hit": False,
                "process_time_ms": 1234,
                "pii_detected": False
            }
        }
    )
    
    response: str = Field(
        ..., 
        description="The AI response text",
        min_length=0,
        max_length=50000
    )
    
    flag: Literal["safe", "blocked", "suspicious", "error", "llm_error"] = Field(
        ...,
        description="Safety flag indicating response status"
    )
    
    reason: Optional[str] = Field(
        None,
        description="Reason for blocking or flagging (if applicable)",
        max_length=500
    )
    
    llm_provider: str = Field(
        ...,
        description="LLM provider used (ollama, openai, gemini, azure)",
        max_length=50
    )
    
    llm_model_name: str = Field(
        ...,
        description="Specific model name used",
        max_length=100
    )
    
    cache_hit: bool = Field(
        default=False,
        description="Whether response was served from cache (always false in OSS)"
    )
    
    process_time_ms: int = Field(
        ...,
        description="Processing time in milliseconds",
        ge=0,
        le=300000  # 5 minutes max
    )
    
    pii_detected: bool = Field(
        default=False,
        description="Whether PII was detected in the request"
    )
    
    pii_types: Optional[List[str]] = Field(
        None,
        description="Types of PII detected (if any)"
    )
    
    confidence_score: Optional[float] = Field(
        None,
        description="Confidence score for classification (if applicable)",
        ge=0.0,
        le=1.0
    )

class ErrorResponse(BaseModel):
    """Standardized error response model"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Authentication failed",
                "code": "AUTH_FAILED",
                "details": {"reason": "Invalid API key"},
                "timestamp": "2025-01-15T10:30:45Z"
            }
        }
    )
    
    error: str = Field(
        ...,
        description="Human-readable error message",
        max_length=500
    )
    
    code: str = Field(
        ...,
        description="Machine-readable error code",
        max_length=50
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Error timestamp in ISO format"
    )

class HealthResponse(BaseModel):
    """Health check response model"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "edition": "oss",
                "uptime_seconds": 3600,
                "llm_status": "available",
                "plugins_loaded": 4
            }
        }
    )
    
    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        ...,
        description="Overall system health status"
    )
    
    version: str = Field(
        ...,
        description="Application version",
        max_length=20
    )
    
    edition: Literal["oss"] = Field(
        default="oss",
        description="Edition type (always 'oss' for open source)"
    )
    
    uptime_seconds: int = Field(
        ...,
        description="System uptime in seconds",
        ge=0
    )
    
    llm_status: Literal["available", "unavailable", "error"] = Field(
        ...,
        description="LLM backend availability status"
    )
    
    plugins_loaded: int = Field(
        ...,
        description="Number of plugins successfully loaded",
        ge=0
    )
    
    error: Optional[str] = Field(
        None,
        description="Error message if status is unhealthy",
        max_length=500
    )

class PluginInfo(BaseModel):
    """Plugin information model"""
    
    name: str = Field(..., description="Plugin name", max_length=100)
    version: Optional[str] = Field(None, description="Plugin version", max_length=20)
    enabled: bool = Field(..., description="Whether plugin is enabled")
    status: Literal["active", "inactive", "error"] = Field(..., description="Plugin status")
    description: Optional[str] = Field(None, description="Plugin description", max_length=200)

class SystemStatusResponse(BaseModel):
    """Detailed system status response"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "edition": "oss",
                "uptime_seconds": 3600,
                "llm": {
                    "provider": "ollama",
                    "model": "mistral",
                    "status": "available"
                },
                "plugins": [
                    {
                        "name": "wag_tail_basic_guard",
                        "enabled": True,
                        "status": "active"
                    }
                ],
                "security": {
                    "pii_detection": True,
                    "code_detection": True,
                    "webhook_enabled": False
                }
            }
        }
    )
    
    status: Literal["healthy", "unhealthy", "degraded"] = Field(
        ...,
        description="Overall system health status"
    )
    
    version: str = Field(..., description="Application version")
    edition: Literal["oss"] = Field(default="oss")
    uptime_seconds: int = Field(..., ge=0)
    
    llm: Dict[str, Any] = Field(
        ...,
        description="LLM configuration and status"
    )
    
    plugins: List[PluginInfo] = Field(
        ...,
        description="List of loaded plugins"
    )
    
    security: Dict[str, Any] = Field(
        ...,
        description="Security features status"
    )

class ValidationError(BaseModel):
    """Validation error details"""
    
    field: str = Field(..., description="Field name with validation error")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value")

class ValidationErrorResponse(BaseModel):
    """Response for validation errors"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation failed",
                "code": "VALIDATION_ERROR",
                "errors": [
                    {
                        "field": "prompt",
                        "message": "Prompt too long",
                        "value": "very long prompt..."
                    }
                ]
            }
        }
    )
    
    error: str = Field(default="Validation failed")
    code: str = Field(default="VALIDATION_ERROR")
    errors: List[ValidationError] = Field(..., description="List of validation errors")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )

# Security-specific response models

class SecurityBlockResponse(BaseModel):
    """Response when request is blocked by security filters"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "blocked": True,
                "reason": "SQL injection pattern detected",
                "filter_type": "regex",
                "pattern_matched": "SELECT * FROM",
                "action": "block"
            }
        }
    )
    
    blocked: bool = Field(default=True, description="Always true for security blocks")
    reason: str = Field(..., description="Reason for blocking", max_length=200)
    filter_type: str = Field(..., description="Type of security filter", max_length=50)
    pattern_matched: Optional[str] = Field(None, description="Pattern that triggered block")
    action: Literal["block", "warn", "log"] = Field(default="block")

class PIIDetectionResponse(BaseModel):
    """Response for PII detection events"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pii_detected": True,
                "pii_types": ["EMAIL_ADDRESS", "PHONE_NUMBER"],
                "entities_count": 2,
                "action": "mask",
                "confidence_scores": [0.95, 0.87]
            }
        }
    )
    
    pii_detected: bool = Field(..., description="Whether PII was detected")
    pii_types: List[str] = Field(..., description="Types of PII detected")
    entities_count: int = Field(..., description="Number of PII entities found", ge=0)
    action: Literal["mask", "block", "redact", "replace"] = Field(default="mask")
    confidence_scores: Optional[List[float]] = Field(
        None,
        description="Confidence scores for each detected entity"
    )

# Webhook-related models

class WebhookRequest(BaseModel):
    """Webhook request payload"""
    
    prompt: str = Field(..., description="User prompt to analyze")
    client_ip: str = Field(..., description="Client IP address")
    api_key_hash: str = Field(..., description="Hashed API key")
    timestamp: str = Field(..., description="Request timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class WebhookResponse(BaseModel):
    """Webhook response from external GuardRail"""
    
    allowed: bool = Field(..., description="Whether request is allowed")
    reason: Optional[str] = Field(None, description="Reason for block/allow")
    confidence: Optional[float] = Field(None, description="Confidence score", ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

# Union types for different response scenarios
ChatEndpointResponse = Union[ChatResponse, ErrorResponse, ValidationErrorResponse]