# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

from wag_tail_logger import logger

def query(prompt: str, timeout: int, api_url: str = None, api_key: str = None, model: str = None, plugins=None) -> dict:
    """
    Query OpenAI LLM (GPT-3.5/4, etc.) with secret lookup via plugins.
    Supports openai>=1.0.0 (new client interface).
    """
    # Use api_key directly if given, else try plugins
    key = api_key
    if not key and plugins is not None:
        for plugin in plugins:
            if hasattr(plugin, "get_secret"):
                try:
                    key = plugin.get_secret("OPENAI_API_KEY")
                    if key:
                        break
                except Exception as e:
                    logger.warning({
                        "message": "Plugin get_secret error",
                        "module": "openai",
                        "event": "get_secret_exception",
                        "error": str(e)
                    })
    if not key:
        logger.info({
            "message": "OPENAI_API_KEY fallback to default",
            "module": "openai",
            "event": "openai_api_key_fallback"
        })
        key = "sk-xxx"  # fallback/dev default

    try:
        import openai
        client = openai.OpenAI(api_key=key)
        model_name = model if model else "gpt-3.5-turbo"
        logger.info({
            "message": f"Calling OpenAI model: {model_name}",
            "module": "openai",
            "event": "llm_call",
            "prompt_summary": prompt[:60]
        })
        
        # O1 models have special requirements
        if model_name.startswith("o1-"):
            # O1 models don't support system messages, temperature, or streaming
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout
                # No temperature, top_p, or other parameters for O1 models
            )
        else:
            # Standard GPT models support all parameters
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
                temperature=0.7,  # Add some creativity
                max_tokens=4000   # Reasonable limit
            )
        # Logging raw response for debug
        logger.debug({
            "message": "OpenAI raw response",
            "module": "openai",
            "raw_response": str(resp)
        })
        answer = resp.choices[0].message.content if resp.choices and resp.choices[0].message else ""
        if answer:
            logger.info({
                "message": "OpenAI LLM call success",
                "module": "openai",
                "event": "llm_response",
                "provider": "openai",
                "model": model_name,
                "response_length": len(answer)
            })
            return {
                "text": answer,
                "usage": getattr(resp, "usage", None),
                "model": model_name
            }
        else:
            logger.error({
                "message": "OpenAI response missing answer text",
                "module": "openai",
                "response": str(resp)
            })
            return {"error": "OpenAI LLM returned no usable text."}
    except Exception as e:
        logger.error({
            "message": "OpenAI query error",
            "module": "openai",
            "event": "query_error",
            "error": str(e)
        })
        return {"error": str(e)}
