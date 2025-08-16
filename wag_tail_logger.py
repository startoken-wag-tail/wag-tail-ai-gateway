# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Logging configuration for Wag-Tail AI Gateway OSS Edition
Secure logging with sensitive data masking
"""

import logging
import logging.handlers
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in log messages"""
    
    def __init__(self):
        super().__init__()
        # Patterns for sensitive data
        self.patterns = [
            # API keys (various formats)
            (re.compile(r'("?api[_-]?key"?\s*[:=]\s*)"[^"]{8,}"', re.IGNORECASE), r'\1"****[MASKED]"'),
            (re.compile(r'("?token"?\s*[:=]\s*)"[^"]{8,}"', re.IGNORECASE), r'\1"****[MASKED]"'),
            (re.compile(r'("?secret"?\s*[:=]\s*)"[^"]{8,}"', re.IGNORECASE), r'\1"****[MASKED]"'),
            (re.compile(r'("?password"?\s*[:=]\s*)"[^"]{8,}"', re.IGNORECASE), r'\1"****[MASKED]"'),
            
            # Bearer tokens
            (re.compile(r'(Bearer\s+)[A-Za-z0-9\-_]{20,}', re.IGNORECASE), r'\1****[MASKED]'),
            
            # Email addresses
            (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '****@****.***'),
            
            # Phone numbers (basic patterns)
            (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '***-***-****'),
            
            # SSN patterns
            (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '***-**-****'),
            
            # Credit card patterns (basic)
            (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '****-****-****-****'),
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and mask sensitive data in log records"""
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            
            # Apply all masking patterns
            for pattern, replacement in self.patterns:
                message = pattern.sub(replacement, message)
            
            # Update the record
            record.msg = message
            record.args = ()
        
        return True

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logger(name: str = "wag_tail") -> logging.Logger:
    """Setup logger with appropriate handlers and formatters"""
    
    # Get logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Load logging configuration
    try:
        from config_loader import get_logging_config
        log_config = get_logging_config()
    except:
        log_config = {
            "level": "INFO",
            "file": "logs/wag_tail_gateway.log",
            "max_size_mb": 50,
            "backup_count": 5,
            "format": "json"
        }
    
    # Set log level
    log_level = getattr(logging, log_config.get("level", "INFO").upper())
    logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # File handler with rotation
    log_file = log_config.get("file", "logs/wag_tail_gateway.log")
    max_bytes = log_config.get("max_size_mb", 50) * 1024 * 1024  # Convert MB to bytes
    backup_count = log_config.get("backup_count", 5)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # Choose formatter
    format_type = log_config.get("format", "json")
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    console_handler.addFilter(sensitive_filter)
    file_handler.addFilter(sensitive_filter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create the main logger instance
logger = setup_logger()

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = setup_logger("wag_tail.security")
    
    def log_blocked_request(self, reason: str, details: Dict[str, Any]):
        """Log a blocked request with security details"""
        self.logger.warning({
            "event": "request_blocked",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **details
        })
    
    def log_pii_detection(self, pii_types: list, details: Dict[str, Any]):
        """Log PII detection event"""
        self.logger.warning({
            "event": "pii_detected",
            "pii_types": pii_types,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **details
        })
    
    def log_security_violation(self, violation_type: str, details: Dict[str, Any]):
        """Log general security violation"""
        self.logger.error({
            "event": "security_violation",
            "violation_type": violation_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **details
        })

# Create security logger instance
security_logger = SecurityLogger()

def mask_sensitive_value(value: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive values for logging"""
    if not value or len(value) <= visible_chars:
        return mask_char * 8
    
    if len(value) <= visible_chars * 2:
        return mask_char * (len(value) - visible_chars) + value[-visible_chars:]
    
    return mask_char * (len(value) - visible_chars) + value[-visible_chars:]

def log_request(
    method: str,
    endpoint: str,
    client_ip: str,
    api_key: Optional[str] = None,
    user_agent: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
):
    """Log incoming request with security context"""
    log_data = {
        "event": "request_received",
        "method": method,
        "endpoint": endpoint,
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if api_key:
        log_data["masked_api_key"] = mask_sensitive_value(api_key)
    
    if user_agent:
        log_data["user_agent"] = user_agent
    
    if extra:
        log_data.update(extra)
    
    logger.info(log_data)

def log_response(
    status_code: int,
    process_time_ms: int,
    response_size: int = 0,
    extra: Optional[Dict[str, Any]] = None
):
    """Log response with performance metrics"""
    log_data = {
        "event": "response_sent",
        "status_code": status_code,
        "process_time_ms": process_time_ms,
        "response_size_bytes": response_size,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if extra:
        log_data.update(extra)
    
    logger.info(log_data)

def log_llm_interaction(
    provider: str,
    model: str,
    prompt_length: int,
    response_length: int,
    process_time_ms: int,
    success: bool,
    error: Optional[str] = None
):
    """Log LLM interaction with performance metrics"""
    log_data = {
        "event": "llm_interaction",
        "provider": provider,
        "model": model,
        "prompt_length": prompt_length,
        "response_length": response_length,
        "process_time_ms": process_time_ms,
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info(log_data)
    else:
        logger.error(log_data)