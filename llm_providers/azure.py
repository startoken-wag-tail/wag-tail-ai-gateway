# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

from wag_tail_logger import logger

def query(prompt: str, timeout: int, api_url: str = None, api_key: str = None, model: str = None, 
          deployment_name: str = None, api_version: str = "2024-02-01", plugins=None) -> dict:
    """
    Query Azure OpenAI/AI Foundry models with deployment-based routing.
    Azure uses deployment names instead of model names directly.
    """
    # Use api_key directly if given, else try plugins (for Vault integration)
    key = api_key
    if not key and plugins is not None:
        for plugin in plugins:
            if hasattr(plugin, "get_secret"):
                try:
                    key = plugin.get_secret("AZURE_OPENAI_API_KEY")
                    if key:
                        break
                except Exception as e:
                    logger.warning({
                        "message": "Plugin get_secret error",
                        "module": "azure",
                        "event": "get_secret_exception",
                        "error": str(e)
                    })
    
    if not key:
        logger.error({"message": "AZURE_OPENAI_API_KEY not found", "module": "azure"})
        return {"error": "Azure OpenAI API key not configured"}

    # Azure requires deployment name, not model name
    deployment = deployment_name or model or "gpt-35-turbo"
    
    # Azure endpoint format: https://YOUR-RESOURCE.openai.azure.com/
    if not api_url:
        logger.error({"message": "Azure endpoint URL not configured", "module": "azure"})
        return {"error": "Azure endpoint URL not configured"}

    try:
        import openai
        from openai import AzureOpenAI
        
        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=key,
            api_version=api_version,
            azure_endpoint=api_url  # e.g., "https://myresource.openai.azure.com/"
        )
        
        logger.info({
            "message": f"Calling Azure OpenAI deployment: {deployment}",
            "module": "azure",
            "event": "llm_call",
            "deployment": deployment,
            "endpoint": api_url,
            "prompt_summary": prompt[:60]
        })
        
        # Azure uses deployment name in the API call
        resp = client.chat.completions.create(
            model=deployment,  # This is the deployment name in Azure
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            temperature=0.7,
            max_tokens=4000
        )
        
        logger.debug({
            "message": "Azure OpenAI raw response",
            "module": "azure",
            "raw_response": str(resp)
        })
        
        answer = resp.choices[0].message.content if resp.choices and resp.choices[0].message else ""
        
        if answer:
            logger.info({
                "message": "Azure OpenAI call success",
                "module": "azure",
                "event": "llm_response",
                "provider": "azure",
                "deployment": deployment,
                "response_length": len(answer)
            })
            return {
                "text": answer,
                "usage": getattr(resp, "usage", None),
                "model": deployment,
                "provider": "azure"
            }
        else:
            logger.error({
                "message": "Azure response missing answer text",
                "module": "azure",
                "response": str(resp)
            })
            return {"error": "Azure OpenAI returned no usable text."}
            
    except Exception as e:
        logger.error({
            "message": "Azure OpenAI query error",
            "module": "azure",
            "event": "query_error",
            "error": str(e),
            "deployment": deployment
        })
        return {"error": str(e)}