# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Response message management for Wag-Tail AI Gateway OSS Edition
Handles response formatting, validation, and logging
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from schemas.response_models import ChatResponse, ErrorResponse, HealthResponse, SystemStatusResponse
from wag_tail_logger import logger, log_response

class ResponseLoader:
    """Manages response formatting and validation"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def create_chat_response(
        self,
        response: str,
        flag: str,
        llm_provider: str,
        llm_model_name: str,
        process_time_ms: int,
        reason: Optional[str] = None,
        pii_detected: bool = False,
        pii_types: Optional[List[str]] = None,
        confidence_score: Optional[float] = None
    ) -> ChatResponse:
        """Create a standardized chat response"""
        
        try:
            chat_response = ChatResponse(
                response=response,
                flag=flag,
                reason=reason,
                llm_provider=llm_provider,
                llm_model_name=llm_model_name,
                cache_hit=False,  # Always false in OSS edition
                process_time_ms=process_time_ms,
                pii_detected=pii_detected,
                pii_types=pii_types,
                confidence_score=confidence_score
            )
            
            # Log the response
            log_response(
                status_code=200,
                process_time_ms=process_time_ms,
                response_size=len(response),
                extra={
                    "flag": flag,
                    "provider": llm_provider,
                    "model": llm_model_name,
                    "pii_detected": pii_detected
                }
            )
            
            return chat_response
            
        except Exception as e:
            logger.error(f"Failed to create chat response: {e}")
            # Return error response instead
            return self.create_error_response(
                error="Response formatting failed",
                code="RESPONSE_ERROR",
                details={"original_error": str(e)}
            )
    
    def create_error_response(
        self,
        error: str,
        code: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ) -> ErrorResponse:
        """Create a standardized error response"""
        
        try:
            error_response = ErrorResponse(
                error=error,
                code=code,
                details=details,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
            
            # Log the error response
            log_response(
                status_code=status_code,
                process_time_ms=0,
                response_size=len(error),
                extra={
                    "error_code": code,
                    "error_details": details
                }
            )
            
            return error_response
            
        except Exception as e:
            logger.error(f"Failed to create error response: {e}")
            # Return minimal error response
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=None
            )
    
    def create_blocked_response(
        self,
        reason: str,
        filter_type: str = "security",
        pattern_matched: Optional[str] = None,
        process_time_ms: int = 0
    ) -> ChatResponse:
        """Create response for blocked requests"""
        
        blocked_message = "Your request has been blocked by our security filters."
        if reason:
            blocked_message += f" Reason: {reason}"
        
        return self.create_chat_response(
            response=blocked_message,
            flag="blocked",
            llm_provider="security_filter",
            llm_model_name="guardrail",
            process_time_ms=process_time_ms,
            reason=reason
        )
    
    def create_llm_error_response(
        self,
        error_message: str,
        llm_provider: str,
        llm_model_name: str,
        process_time_ms: int
    ) -> ChatResponse:
        """Create response for LLM errors"""
        
        return self.create_chat_response(
            response="I'm sorry, I'm currently unable to process your request. Please try again later.",
            flag="llm_error",
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            process_time_ms=process_time_ms,
            reason=error_message
        )
    
    def create_health_response(
        self,
        status: str,
        llm_status: str,
        plugins_loaded: int,
        error: Optional[str] = None
    ) -> HealthResponse:
        """Create health check response"""
        
        uptime_seconds = int(time.time() - self.start_time)
        
        return HealthResponse(
            status=status,
            version="1.0.0",
            edition="oss",
            uptime_seconds=uptime_seconds,
            llm_status=llm_status,
            plugins_loaded=plugins_loaded,
            error=error
        )
    
    def create_system_status_response(
        self,
        status: str,
        llm_info: Dict[str, Any],
        plugins_info: List[Dict[str, Any]],
        security_info: Dict[str, Any]
    ) -> SystemStatusResponse:
        """Create detailed system status response"""
        
        uptime_seconds = int(time.time() - self.start_time)
        
        return SystemStatusResponse(
            status=status,
            version="1.0.0",
            edition="oss",
            uptime_seconds=uptime_seconds,
            llm=llm_info,
            plugins=plugins_info,
            security=security_info
        )
    
    def format_pii_response(
        self,
        original_response: str,
        pii_info: Dict[str, Any],
        llm_provider: str,
        llm_model_name: str,
        process_time_ms: int
    ) -> ChatResponse:
        """Format response when PII is detected"""
        
        pii_detected = pii_info.get("pii_detected", False)
        pii_types = pii_info.get("pii_types", [])
        
        if pii_detected:
            # Log PII detection
            logger.warning(f"PII detected in response: {pii_types}")
            
            # Option 1: Block the response entirely
            # return self.create_blocked_response(
            #     reason=f"Response contains PII: {', '.join(pii_types)}",
            #     filter_type="pii",
            #     process_time_ms=process_time_ms
            # )
            
            # Option 2: Return response with PII warning (current approach)
            return self.create_chat_response(
                response=original_response,  # Could be anonymized version
                flag="suspicious",
                llm_provider=llm_provider,
                llm_model_name=llm_model_name,
                process_time_ms=process_time_ms,
                reason=f"PII detected: {', '.join(pii_types)}",
                pii_detected=True,
                pii_types=pii_types
            )
        else:
            return self.create_chat_response(
                response=original_response,
                flag="safe",
                llm_provider=llm_provider,
                llm_model_name=llm_model_name,
                process_time_ms=process_time_ms,
                pii_detected=False
            )
    
    def validate_response_length(self, response: str, max_length: int = 50000) -> bool:
        """Validate response length"""
        return len(response) <= max_length
    
    def sanitize_response(self, response: str) -> str:
        """Sanitize response content"""
        # Remove any potential script tags or harmful content
        import re
        
        # Remove script tags
        response = re.sub(r'<script[^>]*>.*?</script>', '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove javascript: and vbscript: protocols
        response = re.sub(r'javascript\s*:', '', response, flags=re.IGNORECASE)
        response = re.sub(r'vbscript\s*:', '', response, flags=re.IGNORECASE)
        
        # Remove HTML event handlers
        response = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', response, flags=re.IGNORECASE)
        
        return response
    
    def calculate_process_time(self, start_time: float) -> int:
        """Calculate processing time in milliseconds"""
        return int((time.time() - start_time) * 1000)

# Global response loader instance
response_loader = ResponseLoader()

def get_response_loader() -> ResponseLoader:
    """Get the global response loader instance"""
    return response_loader

# Convenience functions
def create_success_response(
    response: str,
    llm_provider: str,
    llm_model_name: str,
    process_time_ms: int,
    pii_info: Optional[Dict[str, Any]] = None
) -> ChatResponse:
    """Create a successful chat response"""
    if pii_info:
        return response_loader.format_pii_response(
            response, pii_info, llm_provider, llm_model_name, process_time_ms
        )
    else:
        return response_loader.create_chat_response(
            response, "safe", llm_provider, llm_model_name, process_time_ms
        )

def create_blocked_response(reason: str, process_time_ms: int = 0) -> ChatResponse:
    """Create a blocked response"""
    return response_loader.create_blocked_response(reason, process_time_ms=process_time_ms)

def create_error_response(error: str, code: str, details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
    """Create an error response"""
    return response_loader.create_error_response(error, code, details)

def create_llm_error_response(
    error: str,
    llm_provider: str,
    llm_model_name: str,
    process_time_ms: int
) -> ChatResponse:
    """Create an LLM error response"""
    return response_loader.create_llm_error_response(
        error, llm_provider, llm_model_name, process_time_ms
    )

# Legacy function for compatibility with main.py
def load_responses() -> bool:
    """Legacy function for compatibility with main.py"""
    return True