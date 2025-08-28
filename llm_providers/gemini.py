# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

import google.generativeai as genai
from wag_tail_logger import logger

def query(
    prompt: str,
    timeout: int,  # Ignored by Gemini SDK, kept for interface compatibility
    api_key: str = None,
    model: str = "gemini-2.0-flash",
    plugins=None
) -> dict:
    """
    Query Google Gemini LLM via Google Generative AI SDK.
    Supports plugin-based secret lookup and detailed logging.
    Always returns the model name in the result dict.
    """
    key = api_key

    # 1. If missing, try plugin-based secret lookup
    if not key and plugins is not None:
        for plugin in plugins:
            if hasattr(plugin, "get_secret"):
                try:
                    v = plugin.get_secret("GEMINI_API_KEY")
                    if v:
                        key = v
                        logger.info({
                            "message": "GEMINI_API_KEY loaded from plugin",
                            "module": "gemini",
                            "event": "api_key_plugin_lookup"
                        })
                        break
                except Exception as e:
                    logger.warning({
                        "message": "Plugin get_secret error",
                        "module": "gemini",
                        "event": "get_secret_exception",
                        "error": str(e)
                    })

    # 2. Fallback: Log if no key is found
    if not key:
        logger.error({
            "message": "GEMINI_API_KEY is missing, cannot call Gemini",
            "module": "gemini",
            "event": "api_key_missing"
        })
        return {"error": "Gemini API key is missing."}

    try:
        genai.configure(api_key=key)
        model_instance = genai.GenerativeModel(model)
        logger.info({
            "message": f"Calling Gemini model: {model}",
            "module": "gemini",
            "event": "llm_call",
            "prompt_summary": prompt[:60]
        })
        # Call without timeout in generation_config
        response = model_instance.generate_content(prompt)
        logger.debug({
            "message": "Gemini raw response",
            "module": "gemini",
            "raw_response": str(response)
        })

        # Try all known Gemini output formats
        final_text = None
        if hasattr(response, 'text') and response.text:
            final_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            try:
                final_text = response.candidates[0].content.parts[0].text
            except Exception as extract_err:
                logger.warning({
                    "message": "Failed to extract text from candidates",
                    "module": "gemini",
                    "error": str(extract_err)
                })
                final_text = None

        if final_text:
            logger.info({
                "message": "Gemini LLM call success",
                "module": "gemini",
                "event": "llm_response",
                "provider": "gemini",
                "model": model,
                "response_length": len(final_text)
            })
            return {
                "text": final_text,
                "model": model    # <-- Always include model name!
            }
        else:
            logger.error({
                "message": "Gemini response missing answer text",
                "module": "gemini",
                "response": str(response)
            })
            return {"error": "Gemini LLM returned no usable text."}
    except Exception as e:
        logger.error({
            "message": "Gemini query error",
            "module": "gemini",
            "event": "query_error",
            "error": str(e),
            "model": model
        })
        return {"error": str(e)}
