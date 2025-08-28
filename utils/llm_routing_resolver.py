# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""
LLM Routing Resolver - Resolves references in fallback chain to actual provider configurations
"""

import yaml
import os
from typing import List, Dict, Any, Optional
from wag_tail_logger import logger


def resolve_fallback_chain(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Resolves fallback chain references to actual provider configurations.
    
    Converts entries like:
    - {'ref': 'mistral-cluster', 'type': 'instance_group'} 
    - {'ref': 'gemini-flash', 'type': 'model'}
    
    Into actual provider entries like:
    - {'provider': 'ollama', 'model': 'mistral:7b-instruct-q4_K_M', 'api_url': '...', ...}
    
    Args:
        config: The full LLM routing configuration dictionary
        
    Returns:
        List of resolved provider configurations
    """
    fallback_chain = config.get('fallback_chain', [])
    models = config.get('models', [])
    instance_groups = config.get('instance_groups', [])
    
    # Create lookup maps
    models_by_id = {m.get('id'): m for m in models if m.get('id')}
    groups_by_id = {g.get('id'): g for g in instance_groups if g.get('id')}
    
    resolved_chain = []
    
    for entry in fallback_chain:
        if 'ref' in entry:
            # This is a reference that needs to be resolved
            ref = entry['ref']
            ref_type = entry.get('type', 'model')
            
            if ref_type == 'model':
                # Direct model reference
                if ref in models_by_id:
                    model_config = models_by_id[ref].copy()
                    resolved_chain.append(model_config)
                else:
                    logger.warning(f"Model reference '{ref}' not found in models configuration")
                    
            elif ref_type == 'instance_group':
                # Instance group reference - expand to all models in the group
                if ref in groups_by_id:
                    group = groups_by_id[ref]
                    model_refs = group.get('models', [])
                    
                    # Add each model in the group to the chain
                    for model_ref in model_refs:
                        if model_ref in models_by_id:
                            model_config = models_by_id[model_ref].copy()
                            # Mark as part of a group for potential load balancing
                            model_config['_group_id'] = ref
                            resolved_chain.append(model_config)
                        else:
                            logger.warning(f"Model '{model_ref}' in group '{ref}' not found")
                else:
                    logger.warning(f"Instance group reference '{ref}' not found in configuration")
                    
        else:
            # Direct provider configuration (already resolved)
            resolved_chain.append(entry)
    
    logger.debug(f"Resolved fallback chain: {len(resolved_chain)} providers from {len(fallback_chain)} entries")
    
    return resolved_chain


def load_and_resolve_routing_config(path: str = None) -> Dict[str, Any]:
    """
    Loads the LLM routing configuration and resolves all references.
    
    Args:
        path: Path to the LLM routing YAML file (defaults to config/llm_routing.yaml)
        
    Returns:
        Configuration dictionary with resolved fallback_chain
    """
    if not path:
        path = os.path.join("config", "llm_routing.yaml")
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Resolve the fallback chain
        resolved_chain = resolve_fallback_chain(config)
        
        # Create a new config with resolved chain
        resolved_config = config.copy()
        resolved_config['fallback_chain'] = resolved_chain
        
        # Log summary of resolved providers
        providers_summary = []
        for entry in resolved_chain[:5]:  # Log first 5
            provider = entry.get('provider', 'unknown')
            model = entry.get('model', 'unknown')
            providers_summary.append(f"{provider}:{model}")
            
        logger.info({
            "message": "Loaded and resolved LLM routing configuration",
            "total_providers": len(resolved_chain),
            "sample_providers": providers_summary
        })
        
        return resolved_config
        
    except FileNotFoundError:
        logger.error(f"LLM routing config file not found: {path}")
        return {"fallback_chain": []}
    except Exception as e:
        logger.error(f"Failed to load LLM routing config: {e}")
        return {"fallback_chain": []}