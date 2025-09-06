# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

# plugins/key_auth_plugin.py

from plugins.base import PluginBase
from fastapi.responses import JSONResponse
from tools.api_key_auth import lookup_api_key
from wag_tail_logger import logger


class WagTailKeyAuthPlugin(PluginBase):
    __version__ = "4.3.0"
    name = "wag_tail_key_auth"
    
    def on_request(self, request, context):
        # --- Null/Empty Request Validation ---
        if request is None:
            logger.error({
                "message": "Null request object received",
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "Invalid request"}, status_code=400)
        
        if not hasattr(request, 'headers'):
            logger.error({
                "message": "Request object missing headers attribute",
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "Invalid request structure"}, status_code=400)
        
        if request.headers is None:
            logger.error({
                "message": "Request headers is None",
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "No headers in request"}, status_code=400)
        
        # --- Context Validation ---
        if context is None:
            logger.error({
                "message": "Null context object received",
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "Internal server error (context missing)"}, status_code=500)
        
        logger.debug("KeyAuthPlugin.on_request() called with headers: %s", dict(request.headers))
        logger.debug({
            "message": "KeyAuthPlugin.on_request() starting",
            "module": "WagTailKeyAuthPlugin",
            "context_keys": list(context.keys()) if context else None
        })

        # --- Extract and Clean Values ---
        db_engine = context.get("db_engine")
        redis_client = context.get("redis")
        org_id = context.get("org_id")
        api_key = request.headers.get("x-api-key")
        
        # Strip whitespace from string values
        if api_key and isinstance(api_key, str):
            api_key = api_key.strip()
            if not api_key:  # Empty after stripping
                api_key = None
            # Check for null bytes or control characters
            elif '\x00' in api_key or any(ord(c) < 32 for c in api_key):
                logger.warning({
                    "message": "API key contains invalid characters",
                    "module": "WagTailKeyAuthPlugin"
                })
                return JSONResponse({"error": "Invalid API key format"}, status_code=400)
        
        if org_id and isinstance(org_id, str):
            org_id = org_id.strip()
            if not org_id:  # Empty after stripping
                org_id = None

        # --- Check DB connection up ---
        if not db_engine:
            logger.error({
                "message": "DB engine missing! Cannot validate API key.",
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "Internal server error (db connection missing)"}, status_code=500)

        # --- Check Redis (warn but continue) ---
        if not redis_client:
            logger.warning({
                "message": "Redis client missing, falling back to DB-only validation",
                "module": "WagTailKeyAuthPlugin"
            })

        if not api_key or not org_id:
            logger.info({
                "message": "Missing API key or org_id",
                "module": "WagTailKeyAuthPlugin",
                "api_key_present": bool(api_key),
                "org_id_present": bool(org_id)
            })
            return JSONResponse({"error": "Missing API key"}, status_code=401)

        logger.debug({
            "message": "Starting database API key validation",
            "module": "WagTailKeyAuthPlugin",
            "api_key_last6": api_key[-6:] if api_key else None,
            "org_id": org_id
        })

        try:
            # Ensure parameters are not None before calling lookup_api_key
            if api_key is None or org_id is None or db_engine is None:
                logger.error({
                    "message": "Cannot call lookup_api_key with None parameters",
                    "module": "WagTailKeyAuthPlugin",
                    "api_key_none": api_key is None,
                    "org_id_none": org_id is None,
                    "db_engine_none": db_engine is None
                })
                return JSONResponse({"error": "Invalid authentication parameters"}, status_code=400)
            
            result = lookup_api_key(api_key, org_id, db_engine, redis_client)
            
            # Validate result is not None and is a valid response
            if result is None:
                logger.warning({
                    "message": "lookup_api_key returned None",
                    "module": "WagTailKeyAuthPlugin"
                })
                result = False  # Treat None as invalid
                
        except AttributeError as e:
            logger.error({
                "message": "AttributeError in lookup_api_key - likely None parameter",
                "exception": str(e),
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "Invalid authentication configuration"}, status_code=500)
        except TypeError as e:
            logger.error({
                "message": "TypeError in lookup_api_key - parameter type mismatch",
                "exception": str(e),
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "Invalid authentication parameters"}, status_code=400)
        except Exception as e:
            logger.error({
                "message": "Exception while checking API key in DB",
                "exception": str(e),
                "exception_type": type(e).__name__,
                "module": "WagTailKeyAuthPlugin"
            })
            return JSONResponse({"error": "Internal server error (DB query failed)"}, status_code=500)

        logger.debug({
            "message": "Result from lookup_api_key",
            "result": result,
            "api_key": api_key,
            "org_id": org_id
        })

        if result:
            logger.info({
                "message": "API key validated (valid)",
                "module": "WagTailKeyAuthPlugin",
                "org_id": org_id,
                "api_key": api_key
            })
            return None  # Auth OK

        logger.warning({
            "message": "API key rejected (invalid)",
            "module": "WagTailKeyAuthPlugin",
            "org_id": org_id,
            "api_key": api_key
        })
        return JSONResponse({"error": "Invalid API key"}, status_code=401)
