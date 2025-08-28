# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

"""
Authentication utilities for API key validation with fallback strategies
"""
import logging
import yaml
import os
import time
from datetime import datetime
from typing import Optional, Tuple, Dict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("wag_tail_logger")

# In-memory cache for API keys (fallback when database is down)
_api_key_cache = {}
_cache_updated_at = None
_cache_ttl = 300  # 5 minutes

def load_fallback_api_keys() -> Dict:
    """Load API keys from config file as fallback"""
    try:
        fallback_keys = {}
        
        # Load regular config
        config_path = "config/sys_config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Add admin API key
            if 'admin' in config and 'api_key' in config['admin']:
                admin_key = config['admin']['api_key']
                fallback_keys[admin_key] = {
                    'org_id': 'admin',
                    'user_id': 'admin',
                    'status': 'active',
                    'source': 'admin_config'
                }
                
            # Add user API key  
            if 'user_api_key' in config:
                user_key = config['user_api_key']
                fallback_keys[user_key] = {
                    'org_id': 'default',
                    'user_id': 'default_user', 
                    'status': 'active',
                    'source': 'user_config'
                }
        
        # Load internal config
        internal_config_path = "config/internal_config.yaml"
        if os.path.exists(internal_config_path):
            with open(internal_config_path, 'r') as f:
                internal_config = yaml.safe_load(f)
                
            # Add internal API keys
            if 'internal' in internal_config and 'api_keys' in internal_config['internal']:
                for key_info in internal_config['internal']['api_keys']:
                    api_key = key_info.get('key')
                    if api_key:
                        fallback_keys[api_key] = {
                            'org_id': 'INTERNAL',
                            'user_id': key_info.get('description', 'internal_system'),
                            'status': 'active',
                            'source': 'internal_config',
                            'groups': key_info.get('groups', [])
                        }
                        
        return fallback_keys
            
    except Exception as e:
        logger.warning(f"Failed to load fallback API keys from config: {e}")
        
    return {}

def get_license_org_id() -> str:
    """Get org_id from license file as ultimate fallback"""
    try:
        from license_loader import get_org_id
        return get_org_id()
    except Exception as e:
        logger.warning(f"Failed to get org_id from license: {e}")
        return "default_org"

def validate_from_cache(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate API key from in-memory cache"""
    global _api_key_cache, _cache_updated_at
    
    # Check if cache is stale
    current_time = time.time()
    if _cache_updated_at is None or (current_time - _cache_updated_at) > _cache_ttl:
        logger.debug("API key cache is stale, not using cache")
        return False, None, None
        
    if api_key in _api_key_cache:
        cached_data = _api_key_cache[api_key]
        logger.info(f"API key validated from cache: {api_key[-6:]} source={cached_data.get('source')}")
        return True, cached_data.get('org_id'), cached_data.get('user_id')
        
    return False, None, None

def validate_from_fallback_config(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate API key from config file fallback"""
    fallback_keys = load_fallback_api_keys()
    
    if api_key in fallback_keys:
        key_data = fallback_keys[api_key]
        logger.warning(f"API key validated from FALLBACK CONFIG: {api_key[-6:]} (database unavailable)")
        return True, key_data.get('org_id'), key_data.get('user_id')
        
    return False, None, None

def update_cache_from_database(db_engine):
    """Update in-memory cache from database when available"""
    global _api_key_cache, _cache_updated_at
    
    try:
        with db_engine.connect() as conn:
            query = text("SELECT api_key, org_id, user_id, status FROM api_keys WHERE status = 'active'")
            result = conn.execute(query)
            
            new_cache = {}
            for row in result:
                api_key, org_id, user_id, status = row
                new_cache[api_key] = {
                    'org_id': org_id,
                    'user_id': user_id,
                    'status': status,
                    'source': 'database_cache'
                }
                
            _api_key_cache = new_cache
            _cache_updated_at = time.time()
            logger.debug(f"Updated API key cache with {len(new_cache)} keys from database")
            
    except Exception as e:
        logger.warning(f"Failed to update API key cache from database: {e}")

def validate_api_key(api_key: str, db_engine) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Multi-tier API key validation with fallback strategies
    
    Validation Strategy:
    1. Primary: Database lookup (most authoritative)
    2. Secondary: In-memory cache (recent database data)  
    3. Tertiary: Config file fallback (admin/user keys)
    4. Final: Reject (no valid source found)
    
    Args:
        api_key: The API key to validate
        db_engine: Database engine for querying
        
    Returns:
        Tuple of (is_valid, org_id, user_id)
    """
    if not api_key:
        return False, None, None
    
    # Tier 1: Try database first (most authoritative)
    if db_engine:
        try:
            with db_engine.connect() as conn:
                query = text("""
                    SELECT org_id, user_id, status, expires_at 
                    FROM api_keys 
                    WHERE api_key = :api_key
                """)
                result = conn.execute(query, {"api_key": api_key})
                row = result.fetchone()
                
                if row:
                    org_id, user_id, status, expires_at = row
                    
                    # Check if key is active and not expired
                    if status == 'active' and (not expires_at or expires_at > datetime.now()):
                        # Update cache for future use
                        try:
                            update_cache_from_database(db_engine)
                        except:
                            pass  # Don't fail if cache update fails
                            
                        # Update last_used_at
                        try:
                            update_query = text("""
                                UPDATE api_keys 
                                SET last_used_at = CURRENT_TIMESTAMP 
                                WHERE api_key = :api_key
                            """)
                            conn.execute(update_query, {"api_key": api_key})
                            conn.commit()
                        except:
                            pass  # Don't fail if last_used update fails
                            
                        logger.debug(f"API key validated from DATABASE: {api_key[-6:]}")
                        return True, org_id, user_id
                    else:
                        logger.warning(f"API key inactive or expired: {api_key[-6:]} status={status}")
                        return False, None, None
                else:
                    logger.debug(f"API key not found in database: {api_key[-6:]}")
                    
        except SQLAlchemyError as e:
            logger.warning(f"Database error, trying fallback: {e}")
        except Exception as e:
            logger.warning(f"Database connection failed, trying fallback: {e}")
    
    # Tier 2: Try in-memory cache (recent database data)
    is_valid, org_id, user_id = validate_from_cache(api_key)
    if is_valid:
        return True, org_id, user_id
    
    # Tier 3: Try config file fallback (for critical admin/user keys)
    is_valid, org_id, user_id = validate_from_fallback_config(api_key)
    if is_valid:
        return True, org_id, user_id
    
    # Tier 4: All validation methods failed
    logger.warning(f"API key validation failed on all tiers: {api_key[-6:]}")
    return False, None, None

def mask_api_key(api_key: str) -> str:
    """Mask API key for logging"""
    if not api_key or len(api_key) < 8:
        return "***"
    return "****" + api_key[-6:]