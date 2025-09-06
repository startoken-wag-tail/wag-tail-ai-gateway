# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Header-based LLM Model Selection for Wag Tail AI Gateway

Allows users to specify provider/model via headers:
- x-llm-provider: Provider name (openai, azure, gemini, mistral)  
- x-llm-model: Model name (gpt-4, gemini-pro, etc.)
- x-provider: Alternative header name for provider
- x-model: Alternative header name for model
"""

from typing import Optional, Dict, List, Tuple
from fastapi import Request
from wag_tail_logger import logger
from config_loader import load_config


class HeaderModelSelector:
    """Handles header-based model selection with configuration validation"""
    
    def __init__(self):
        self.config = load_config()
        self.available_providers = self._load_available_providers()
    
    def _load_available_providers(self) -> Dict[str, Dict]:
        """Load available providers from configuration"""
        config = self.config
        
        # For basic edition - load from sys_config.yaml
        if "llm" in config and "available_providers" in config["llm"]:
            return config["llm"]["available_providers"]
        
        # For advanced edition - extract from llm_routing.yaml
        # This would be loaded by the routing plugin, so we'll provide fallback
        return {
            "mistral": {
                "models": ["mistral"],
                "enabled": True
            },
            "openai": {
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini"],
                "enabled": True
            },
            "azure": {
                "models": ["gpt-4o", "gpt-4-turbo", "gpt-35-turbo"],
                "enabled": True
            },
            "gemini": {
                "models": ["gemini-2.0-flash"],
                "enabled": True
            }
        }
    
    def extract_model_headers(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        """Extract provider and model from request headers"""
        headers = request.headers
        
        # Try primary header names
        provider = headers.get("x-llm-provider")
        model = headers.get("x-llm-model")
        
        # Try alternative header names if primary not found
        if not provider:
            provider = headers.get("x-provider")
        if not model:
            model = headers.get("x-model")
        
        return provider, model
    
    def validate_provider_model(self, provider: str, model: str, org_id: str = None) -> Tuple[bool, str]:
        """Validate that the requested provider/model combination is allowed"""
        
        if not provider or not model:
            return False, "Both provider and model must be specified"
        
        # Check if provider is available
        if provider not in self.available_providers:
            available = list(self.available_providers.keys())
            return False, f"Provider '{provider}' not available. Available: {available}"
        
        provider_config = self.available_providers[provider]
        
        # Check if provider is enabled
        if not provider_config.get("enabled", True):
            return False, f"Provider '{provider}' is disabled"
        
        # Check if model is available for this provider
        available_models = provider_config.get("models", [])
        if model not in available_models:
            return False, f"Model '{model}' not available for provider '{provider}'. Available: {available_models}"
        
        return True, "Valid"
    
    def create_override_chain(self, provider: str, model: str, org_id: str = None) -> List[Dict]:
        """Create a fallback chain with the specified provider/model as primary"""
        
        # Get provider configuration
        provider_config = self.available_providers.get(provider, {})
        
        # Create primary entry with requested provider/model
        primary_entry = {
            "provider": provider,
            "model": model,
            "timeout": provider_config.get("timeout", 60)
        }
        
        # Add provider-specific configuration
        if "api_url" in provider_config:
            primary_entry["api_url"] = provider_config["api_url"]
        if "api_key" in provider_config:
            primary_entry["api_key"] = provider_config["api_key"]
        if "api_version" in provider_config:  # For Azure
            primary_entry["api_version"] = provider_config["api_version"]
        if "deployment_name" in provider_config:  # For Azure
            primary_entry["deployment_name"] = provider_config["deployment_name"]
        
        # Create fallback chain with requested model first, then defaults
        override_chain = [primary_entry]
        
        # Add fallback options (could be from original fallback_chain)
        # For now, just add mistral as fallback if it's not the requested provider
        if provider != "mistral" and "mistral" in self.available_providers:
            fallback_entry = {
                "provider": "mistral",
                "model": "mistral",
                "api_url": "http://localhost:11434/api/generate",
                "timeout": 60,
                "api_key": ""
            }
            override_chain.append(fallback_entry)
        
        return override_chain
    
    def process_request_headers(self, request: Request, context: Dict, org_id: str = None) -> Dict:
        """Process request headers and modify context if model override is requested"""
        
        provider, model = self.extract_model_headers(request)
        
        if not provider and not model:
            # No override requested, use default behavior
            return context
        
        if not provider or not model:
            # Incomplete override - log detailed error for monitoring
            logger.error({
                "message": "🚫 INCOMPLETE LLM HEADER SPECIFICATION",
                "event": "incomplete_llm_override_headers",
                "org_id": org_id,
                "provided_provider": provider,
                "provided_model": model,
                "missing_headers": [
                    "x-llm-provider" if not provider else None,
                    "x-llm-model" if not model else None
                ],
                "required_headers": ["x-llm-provider", "x-llm-model"],
                "alternative_headers": ["x-provider", "x-model"],
                "fallback_behavior": "Using default LLM routing configuration"
            })
            
            # Also log simpler warning
            logger.warning({
                "message": f"Incomplete LLM headers from org '{org_id}' - provider: {provider}, model: {model}",
                "event": "llm_override_incomplete",
                "org_id": org_id
            })
            return context
        
        # Validate the requested provider/model
        is_valid, message = self.validate_provider_model(provider, model, org_id)
        
        if not is_valid:
            # Log detailed error for monitoring and debugging
            logger.error({
                "message": "🚫 INVALID LLM MODEL SPECIFICATION",
                "event": "invalid_llm_override_request",
                "org_id": org_id,
                "requested_provider": provider,
                "requested_model": model,
                "validation_error": message,
                "available_providers": list(self.available_providers.keys()),
                "available_models_for_provider": self.available_providers.get(provider, {}).get("models", []) if provider in self.available_providers else [],
                "fallback_behavior": "Using default LLM routing configuration",
                "client_headers": {
                    "x-llm-provider": provider,
                    "x-llm-model": model
                }
            })
            
            # Also log a simpler warning for general monitoring
            logger.warning({
                "message": f"Invalid model '{model}' requested for provider '{provider}' by org '{org_id}' - falling back to defaults",
                "event": "llm_override_fallback",
                "org_id": org_id,
                "requested": f"{provider}/{model}",
                "reason": message
            })
            return context
        
        # Create override chain
        override_chain = self.create_override_chain(provider, model, org_id)
        
        # Update context with override
        context["llm_override_requested"] = True
        context["requested_provider"] = provider
        context["requested_model"] = model
        context["fallback_chain"] = override_chain
        context["llm_routing_config"] = {
            "fallback_chain": override_chain
        }
        
        logger.info({
            "message": "✅ LLM OVERRIDE SUCCESSFULLY APPLIED",
            "event": "llm_override_applied",
            "org_id": org_id,
            "requested_provider": provider,
            "requested_model": model,
            "fallback_chain_length": len(override_chain),
            "primary_provider": override_chain[0].get("provider") if override_chain else None,
            "primary_model": override_chain[0].get("model") if override_chain else None,
            "has_fallback_providers": len(override_chain) > 1
        })
        
        return context


# Global instance for use in main.py
header_model_selector = HeaderModelSelector()


def apply_model_header_overrides(request: Request, context: Dict, org_id: str = None) -> Dict:
    """Convenience function to apply model header overrides to context"""
    return header_model_selector.process_request_headers(request, context, org_id)