# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Enhanced Configuration Loader for Wag-Tail AI Gateway OSS Edition
Supports environment-specific configurations, deep merging, and validation
"""

import yaml
import os
import copy
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass

class ConfigurationLoader:
    """Enhanced configuration loader with environment support for OSS edition"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.environment = self._detect_environment()
        self._config_cache = None
        
    def _detect_environment(self) -> str:
        """Detect current environment from environment variables"""
        env = os.getenv("WAGTAIL_ENVIRONMENT", "development").lower()
        valid_envs = ["development", "staging", "production", "test"]
        
        if env not in valid_envs:
            logger.warning(f"Unknown environment '{env}', defaulting to 'development'")
            return "development"
        
        return env
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration with environment-specific overrides"""
        
        # Check if we can use cached config (production only)
        if not force_reload and self._config_cache and self.environment == "production":
            return copy.deepcopy(self._config_cache)
        
        try:
            # 1. Load base configuration
            base_config = self._load_base_config()
            
            # 2. Load environment-specific overrides
            env_config = self._load_environment_config()
            
            # 3. Deep merge configurations
            merged_config = self._deep_merge(base_config, env_config)
            
            # 4. Apply environment variable overrides
            final_config = self._apply_env_overrides(merged_config)
            
            # 5. Validate configuration
            self._validate_configuration(final_config)
            
            # 6. Cache configuration (production only)
            if self.environment == "production":
                self._config_cache = copy.deepcopy(final_config)
            
            logger.info(f"Configuration loaded successfully for environment: {self.environment}")
            
            return final_config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration file"""
        base_config_path = self.config_dir / "sys_config.yaml"
        
        if not base_config_path.exists():
            logger.warning(f"Base config file not found: {base_config_path}")
            return self._get_default_config()
        
        try:
            with open(base_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Loaded base config from {base_config_path}")
                return config or {}
        except Exception as e:
            logger.error(f"Failed to load base config: {e}")
            raise ConfigurationError(f"Invalid base configuration: {e}")
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        env_config_path = self.config_dir / "environments" / f"{self.environment}.yaml"
        
        if not env_config_path.exists():
            logger.info(f"No environment config found for '{self.environment}' at {env_config_path}")
            return {}
        
        try:
            with open(env_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Loaded environment config from {env_config_path}")
                return config or {}
        except Exception as e:
            logger.error(f"Failed to load environment config: {e}")
            raise ConfigurationError(f"Invalid environment configuration: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence"""
        result = copy.deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        
        # Core application settings
        if os.getenv("WAGTAIL_HOST"):
            config.setdefault("app", {})["host"] = os.getenv("WAGTAIL_HOST")
        
        if os.getenv("WAGTAIL_PORT"):
            config.setdefault("app", {})["port"] = int(os.getenv("WAGTAIL_PORT"))
        
        if os.getenv("WAGTAIL_DEBUG"):
            config.setdefault("app", {})["debug"] = os.getenv("WAGTAIL_DEBUG").lower() in ("true", "1", "yes")
        
        # LLM configuration overrides
        if os.getenv("WAGTAIL_LLM_PROVIDER"):
            config.setdefault("llm", {})["provider"] = os.getenv("WAGTAIL_LLM_PROVIDER")
        
        if os.getenv("WAGTAIL_LLM_MODEL"):
            config.setdefault("llm", {})["model"] = os.getenv("WAGTAIL_LLM_MODEL")
        
        if os.getenv("WAGTAIL_LLM_API_KEY"):
            config.setdefault("llm", {})["api_key"] = os.getenv("WAGTAIL_LLM_API_KEY")
        
        if os.getenv("WAGTAIL_LLM_API_URL"):
            config.setdefault("llm", {})["api_url"] = os.getenv("WAGTAIL_LLM_API_URL")
        
        # OpenAI specific
        if os.getenv("OPENAI_API_KEY"):
            config.setdefault("llm", {})["api_key"] = os.getenv("OPENAI_API_KEY")
        
        # Gemini specific  
        if os.getenv("GEMINI_API_KEY"):
            config.setdefault("llm", {})["api_key"] = os.getenv("GEMINI_API_KEY")
        
        # Azure specific
        if os.getenv("AZURE_OPENAI_API_KEY"):
            config.setdefault("llm", {})["api_key"] = os.getenv("AZURE_OPENAI_API_KEY")
        
        if os.getenv("AZURE_OPENAI_ENDPOINT"):
            config.setdefault("llm", {})["api_url"] = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        # Anthropic specific
        if os.getenv("ANTHROPIC_API_KEY"):
            config.setdefault("llm", {})["api_key"] = os.getenv("ANTHROPIC_API_KEY")
        
        # Ollama configuration
        if os.getenv("OLLAMA_URL"):
            config.setdefault("llm", {})["api_url"] = os.getenv("OLLAMA_URL")
        
        # Logging overrides
        if os.getenv("WAGTAIL_LOGGING_LEVEL"):
            config.setdefault("logging", {})["level"] = os.getenv("WAGTAIL_LOGGING_LEVEL")
        
        if os.getenv("LOG_LEVEL"):
            config.setdefault("logging", {})["level"] = os.getenv("LOG_LEVEL")
        
        if os.getenv("LOG_FORMAT"):
            config.setdefault("logging", {})["format"] = os.getenv("LOG_FORMAT")
        
        # API configuration
        if os.getenv("WAGTAIL_API_KEY"):
            config.setdefault("api", {})["default_api_key"] = os.getenv("WAGTAIL_API_KEY")
        
        if os.getenv("DEFAULT_API_KEY"):
            config.setdefault("api", {})["default_api_key"] = os.getenv("DEFAULT_API_KEY")
        
        # Webhook configuration
        if os.getenv("WAGTAIL_WEBHOOK_URL"):
            config.setdefault("webhook", {})["url"] = os.getenv("WAGTAIL_WEBHOOK_URL")
            config.setdefault("webhook", {})["enabled"] = True
        
        if os.getenv("WAGTAIL_WEBHOOK_SECRET"):
            config.setdefault("webhook", {})["hmac_secret"] = os.getenv("WAGTAIL_WEBHOOK_SECRET")
        
        if os.getenv("WEBHOOK_SECRET"):
            config.setdefault("webhook", {})["hmac_secret"] = os.getenv("WEBHOOK_SECRET")
        
        # Security configuration
        if os.getenv("ENABLE_PII_DETECTION"):
            config.setdefault("security", {})["enable_pii_detection"] = \
                os.getenv("ENABLE_PII_DETECTION").lower() in ("true", "1", "yes")
        
        if os.getenv("ENABLE_CODE_DETECTION"):
            config.setdefault("security", {})["enable_code_detection"] = \
                os.getenv("ENABLE_CODE_DETECTION").lower() in ("true", "1", "yes")
        
        if os.getenv("MAX_PROMPT_LENGTH"):
            config.setdefault("security", {})["max_prompt_length"] = int(os.getenv("MAX_PROMPT_LENGTH"))
        
        return config
    
    def _validate_configuration(self, config: Dict[str, Any]) -> None:
        """Validate configuration for current environment"""
        
        # Validate required sections for OSS
        required_sections = ["llm", "security", "logging"]
        for section in required_sections:
            if section not in config:
                logger.warning(f"Missing configuration section: {section}")
                # Don't raise error for missing sections in OSS, just warn
        
        # Environment-specific validations
        if self.environment == "production":
            self._validate_production_config(config)
        
        # Validate LLM configuration
        self._validate_llm_config(config)
    
    def _validate_production_config(self, config: Dict[str, Any]) -> None:
        """Production-specific configuration validation"""
        
        # Security requirements for production
        api_config = config.get("api", {})
        
        if api_config.get("default_api_key") in ["demo-key-for-testing", "test-key"]:
            raise ConfigurationError("Default test API key detected in production")
        
        # LLM requirements
        llm_config = config.get("llm", {})
        if llm_config.get("provider") == "ollama" and not llm_config.get("api_url"):
            logger.warning("Ollama provider configured but no API URL specified")
        
        # Logging requirements
        logging_config = config.get("logging", {})
        if logging_config.get("level") == "DEBUG":
            logger.warning("DEBUG logging enabled in production")
    
    def _validate_llm_config(self, config: Dict[str, Any]) -> None:
        """Validate LLM configuration"""
        llm_config = config.get("llm", {})
        
        if not llm_config:
            logger.warning("No LLM configuration found")
            return
        
        provider = llm_config.get("provider")
        if not provider:
            logger.warning("No LLM provider specified")
            return
        
        # Validate provider-specific requirements
        if provider in ["openai", "gemini", "azure", "anthropic"]:
            if not llm_config.get("api_key"):
                logger.warning(f"No API key configured for {provider}")
        
        elif provider == "ollama":
            if not llm_config.get("api_url"):
                logger.warning("No API URL configured for Ollama")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return minimal default configuration when no config file is found"""
        return {
            "edition": "oss",
            "environment": self.environment,
            "llm": {
                "provider": "ollama",
                "model": "mistral", 
                "api_url": "http://localhost:11434/api/generate",
                "api_key": "",
                "timeout": 60
            },
            "security": {
                "enable_pii_detection": True,
                "enable_code_detection": True,
                "max_prompt_length": 10000
            },
            "api": {
                "default_api_key": "demo-key-for-testing"
            },
            "logging": {
                "level": "DEBUG" if self.environment == "development" else "INFO",
                "file": "logs/wag_tail_gateway.log",
                "format": "text" if self.environment == "development" else "json"
            },
            "plugins": {
                "enabled": [
                    "wag_tail_key_auth",
                    "wag_tail_basic_guard", 
                    "wag_tail_pii_guard",
                    "wag_tail_webhook_guardrail"
                ]
            },
            "webhook": {
                "enabled": False,
                "url": "",
                "timeout": 10,
                "retry_attempts": 2,
                "hmac_secret": ""
            }
        }
    
    def get_environment(self) -> str:
        """Get current environment"""
        return self.environment
    
    def reload_config(self) -> Dict[str, Any]:
        """Force reload configuration"""
        logger.info("Reloading configuration...")
        return self.load_config(force_reload=True)

# Global configuration loader instance
_config_loader = ConfigurationLoader()

def load_config() -> Dict[str, Any]:
    """Load configuration (main entry point)"""
    return _config_loader.load_config()

def get_environment() -> str:
    """Get current environment"""
    return _config_loader.get_environment()

def reload_config() -> Dict[str, Any]:
    """Reload configuration"""
    return _config_loader.reload_config()

# Convenience functions for specific configuration sections
def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration"""
    config = load_config()
    return config.get("llm", {})

def get_security_config() -> Dict[str, Any]:
    """Get security configuration"""
    config = load_config()
    return config.get("security", {})

def get_api_config() -> Dict[str, Any]:
    """Get API configuration"""
    config = load_config()
    return config.get("api", {})

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration""" 
    config = load_config()
    return config.get("logging", {})

def get_webhook_config() -> Dict[str, Any]:
    """Get webhook configuration"""
    config = load_config()
    return config.get("webhook", {})

def get_plugin_config() -> Dict[str, Any]:
    """Get plugin configuration"""
    config = load_config()
    return config.get("plugins", {})

def is_plugin_enabled(plugin_name: str) -> bool:
    """Check if a specific plugin is enabled"""
    plugin_config = get_plugin_config()
    enabled_plugins = plugin_config.get("enabled", [])
    return plugin_name in enabled_plugins

def get_default_api_key() -> Optional[str]:
    """Get the default API key for testing"""
    api_config = get_api_config()
    return api_config.get("default_api_key")

def validate_config() -> bool:
    """Validate configuration and return True if valid"""
    try:
        config = load_config()
        
        # Check required LLM configuration
        llm_config = config.get("llm", {})
        if not llm_config.get("provider"):
            return False
        
        # Validate provider-specific requirements
        provider = llm_config.get("provider")
        if provider in ["openai", "gemini", "azure", "anthropic"]:
            if not llm_config.get("api_key"):
                return False
        
        if provider == "azure":
            if not llm_config.get("api_url"):
                return False
        
        return True
        
    except Exception:
        return False

# Legacy compatibility functions (for backward compatibility)
def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function - use the class method instead"""
    return _config_loader._apply_env_overrides(config)

def _get_default_config() -> Dict[str, Any]:
    """Legacy function - use the class method instead"""
    return _config_loader._get_default_config()