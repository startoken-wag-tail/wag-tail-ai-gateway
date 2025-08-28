# Copyright (c) 2025 Startoken Pty Ltd
# SPDX-License-Identifier: Apache-2.0

def get_llm_client(provider_name: str):
    if provider_name == "mistral":
        from . import mistral
        return mistral
    elif provider_name == "openai":
        from . import openai
        return openai
    elif provider_name == "gemini":
        from . import gemini
        return gemini
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
