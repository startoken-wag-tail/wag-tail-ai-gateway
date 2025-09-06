# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
Simplified Configuration Loader for Wag-Tail AI Gateway
Each environment has its own independent sys_config.yaml file
"""

import yaml
import os
import copy
from typing import Dict, Any, Optional
from pathlib import Path
from wag_tail_logger import get_logger

# Get wag_tail logger
logger = get_logger()

class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass

class ConfigurationLoader:
    """Simplified configuration loader - one config file per deployment"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._config_cache = None
        self._last_loaded = None
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration from sys_config.yaml"""
        
        # Check if we can use cached config
        if not force_reload and self._config_cache:
            return copy.deepcopy(self._config_cache)
        
        try:
            # Load base configuration
            config = self._load_base_config()
            
            # Apply environment variable overrides
            final_config = self._apply_env_overrides(config)
            
            # Validate configuration
            self._validate_configuration(final_config)
            
            # Cache configuration
            self._config_cache = copy.deepcopy(final_config)
            self._last_loaded = final_config
            
            logger.info("Configuration loaded successfully")
            return final_config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load the main sys_config.yaml file"""
        config_path = self.config_dir / "sys_config.yaml"
        
        if not config_path.exists():
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Loaded configuration from {config_path}")
                return config or {}
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            raise ConfigurationError(f"Invalid configuration file: {e}")
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        result = copy.deepcopy(config)
        
        # Common environment variable overrides
        env_overrides = {
            'WAGTAIL_DATABASE_HOST': ['database', 'host'],
            'WAGTAIL_DATABASE_PORT': ['database', 'port'],
            'WAGTAIL_DATABASE_NAME': ['database', 'name'],
            'WAGTAIL_DATABASE_USER': ['database', 'user'],
            'WAGTAIL_DATABASE_PASSWORD': ['database', 'password'],
            'WAGTAIL_LLM_PROVIDER': ['llm', 'provider'],
            'WAGTAIL_LLM_MODEL': ['llm', 'model'],
            'WAGTAIL_LLM_API_KEY': ['llm', 'api_key'],
            'WAGTAIL_LOG_LEVEL': ['logging', 'level'],
            'WAGTAIL_PORT': ['server', 'port'],
        }
        
        for env_var, config_path in env_overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the config section and set the value
                current = result
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Convert port to int if needed
                if config_path[-1] == 'port':
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid port value in {env_var}: {value}")
                        continue
                
                current[config_path[-1]] = value
                logger.debug(f"Applied env override: {env_var} -> {'.'.join(config_path)}")
        
        return result
    
    def _validate_configuration(self, config: Dict[str, Any]) -> None:
        """Validate the loaded configuration"""
        
        # Validate required sections exist
        required_sections = ['server', 'security', 'logging']
        for section in required_sections:
            if section not in config:
                logger.warning(f"Missing configuration section: {section}")
        
        # Validate server configuration
        server_config = config.get('server', {})
        if 'port' not in server_config:
            logger.warning("Server port not specified, will use default")
        
        # Validate security configuration
        security_config = config.get('security', {})
        if not security_config.get('api_keys', {}).get('default_key'):
            logger.warning("No default API key configured")
        
        # Validate database configuration if present
        db_config = config.get('database', {})
        if db_config and not db_config.get('host'):
            logger.warning("Database configured but no host specified")
        
        # Validate LLM configuration
        llm_config = config.get('llm', {})
        if llm_config and not llm_config.get('provider'):
            logger.warning("LLM configuration present but no provider specified")
        
        logger.debug("Configuration validation completed")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if no config file exists"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True,
                "workers": 1
            },
            "security": {
                "api_keys": {
                    "default_key": "dev-key-12345"
                },
                "rate_limiting": {
                    "enabled": False
                }
            },
            "logging": {
                "level": "INFO",
                "format": "text"
            },
            "database": {
                "type": "sqlite",
                "path": "data/wag_tail.db"
            }
        }
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get a specific configuration value using dot notation (e.g., 'server.port')"""
        if self._last_loaded is None:
            self.load_config()
        
        keys = key_path.split('.')
        current = self._last_loaded
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def reload_config(self) -> Dict[str, Any]:
        """Force reload configuration from disk"""
        return self.load_config(force_reload=True)

# Global configuration loader instance
config_loader = ConfigurationLoader()

def get_config() -> Dict[str, Any]:
    """Get the current configuration"""
    return config_loader.load_config()

def get_config_value(key_path: str, default: Any = None) -> Any:
    """Get a specific configuration value"""
    return config_loader.get_config_value(key_path, default)

def reload_config() -> Dict[str, Any]:
    """Reload configuration from disk"""
    return config_loader.reload_config()

# Legacy compatibility functions
def load_config() -> Dict[str, Any]:
    """Legacy compatibility function - use get_config() instead"""
    return get_config()

def get_admin_api_key() -> Optional[str]:
    """Get admin API key (legacy compatibility)"""
    config = get_config()
    return config.get("admin", {}).get("api_key") or \
           config.get("security", {}).get("api_keys", {}).get("admin_key")

def is_plugins_enabled() -> bool:
    """Check if plugins are enabled (legacy compatibility)"""
    config = get_config()
    return bool(config.get("plugins", {}).get("enabled", True))

# Group and database configuration functions
def get_group_config() -> Dict[str, Any]:
    """Get group configuration from group_config.yaml"""
    try:
        from group_loader import load_group_config
        return load_group_config()
    except ImportError:
        return {}

def get_db_config() -> Dict[str, Any]:
    """Get database configuration"""
    config = get_config()
    return config.get("database", {"path": "data/wag_tail.db"})

# Configuration validation function
def validate_config() -> bool:
    """Validate current configuration"""
    try:
        config_loader.load_config()
        return True
    except ConfigurationError:
        return False