# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Header-based LLM Model Selection for Wag Tail AI Gateway - OSS Edition

Allows users to specify provider/model via headers:
- x-llm-provider: Provider name (openai, azure, gemini, mistral)  
- x-llm-model: Model name (gpt-4, gemini-pro, etc.)
"""

from typing import Optional, Dict
from wag_tail_logger import logger
from config_loader import load_config


def apply_model_header_overrides(context: Dict, provider: Optional[str], model: Optional[str]) -> Dict:
    """
    Apply model header overrides to context for OSS edition
    
    Args:
        context: Request context dictionary
        provider: LLM provider from x-llm-provider header
        model: LLM model from x-llm-model header
    
    Returns:
        Updated context with LLM overrides
    """
    
    if not provider and not model:
        # No override requested, use default behavior
        return context
    
    if provider and model:
        # Both provider and model specified - apply override
        context["llm_override_requested"] = True
        context["llm_provider"] = provider
        context["llm_model"] = model
        
        logger.info({
            "message": "LLM header override applied",
            "provider": provider,
            "model": model,
            "edition": "oss"
        })
    else:
        # Incomplete override - log warning but continue with defaults
        logger.warning({
            "message": "Incomplete LLM header override",
            "provider": provider,
            "model": model,
            "note": "Both x-llm-provider and x-llm-model headers required"
        })
    
    return context