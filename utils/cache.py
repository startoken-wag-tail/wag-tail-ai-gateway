# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
from utils.redis_client import r
from wag_tail_logger import logger  # Use project logger

# Module-global cache health flag
cache_available = True

def get_cache_key(org_id, group_id, prompt):
    gid = group_id or ""  # Avoid literal "None" in key
    base = f"{org_id}:{gid}:{prompt}"
    key = "cache:" + hashlib.sha256(base.encode("utf-8")).hexdigest()
    logger.debug(f"[CACHE] get_cache_key: base={base!r} key={key}")
    return key

def cache_get(org_id, group_id, prompt, edition="basic"):
    global cache_available
    key = get_cache_key(org_id, group_id, prompt)
    try:
        result = r.get(key)
        cache_available = True  # Reset flag on success
        if result:
            logger.debug(f"[CACHE GET] HIT key={key} org_id={org_id} group_id={group_id} prompt={prompt!r}")
            return json.loads(result)
        else:
            logger.debug(f"[CACHE GET] MISS key={key} org_id={org_id} group_id={group_id} prompt={prompt!r}")
        return None
    except Exception as e:
        cache_available = False
        msg = f"[CACHE GET] Redis error for key={key}: {str(e)}"
        if edition == "advanced":
            logger.error(msg + " (advanced user: group rate limit and cache unavailable!)")
        else:
            logger.warning(msg)
        return None

def cache_set(org_id, group_id, prompt, response, ttl=3600, edition="basic"):
    global cache_available
    key = get_cache_key(org_id, group_id, prompt)
    try:
        logger.debug(f"[CACHE SET] key={key} org_id={org_id} group_id={group_id} prompt={prompt!r} ttl={ttl}")
        r.set(key, json.dumps(response), ex=ttl)
        cache_available = True  # Reset flag on success
    except Exception as e:
        cache_available = False
        msg = f"[CACHE SET] Redis error for key={key}: {str(e)}"
        if edition == "advanced":
            logger.error(msg + " (advanced user: group rate limit and cache unavailable!)")
        else:
            logger.warning(msg)

def is_cache_available():
    """Expose cache/Redis health for use in API responses."""
    return cache_available
