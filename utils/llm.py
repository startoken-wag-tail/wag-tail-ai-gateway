# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Wag-Tail Pty Ltd

"""
LLM provider integration for Wag-Tail AI Gateway OSS Edition
Supports Ollama, OpenAI, Gemini, and Azure OpenAI
"""

import json
import time
import requests
from typing import Dict, Any, Optional, Tuple
from config_loader import get_llm_config
from wag_tail_logger import logger, log_llm_interaction

class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("provider", "ollama")
        self.model = config.get("model", "mistral")
        self.api_key = config.get("api_key", "")
        self.api_url = config.get("api_url", "")
        self.timeout = config.get("timeout", 60)
    
    def generate_response(self, prompt: str) -> Tuple[str, bool, Optional[str]]:
        """Generate response from LLM. Returns (response, success, error)"""
        raise NotImplementedError
    
    def test_connection(self) -> bool:
        """Test if LLM is accessible"""
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not self.api_url:
            self.api_url = "http://localhost:11434/api/generate"
    
    def generate_response(self, prompt: str) -> Tuple[str, bool, Optional[str]]:
        """Generate response using Ollama"""
        start_time = time.time()
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            process_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "")
                
                log_llm_interaction(
                    provider="ollama",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=len(llm_response),
                    process_time_ms=process_time_ms,
                    success=True
                )
                
                return llm_response, True, None
            else:
                error_msg = f"Ollama error: {response.status_code} - {response.text}"
                log_llm_interaction(
                    provider="ollama",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=0,
                    process_time_ms=process_time_ms,
                    success=False,
                    error=error_msg
                )
                return "", False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "Ollama request timeout"
            log_llm_interaction(
                provider="ollama",
                model=self.model,
                prompt_length=len(prompt),
                response_length=0,
                process_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error=error_msg
            )
            return "", False, error_msg
            
        except Exception as e:
            error_msg = f"Ollama error: {str(e)}"
            log_llm_interaction(
                provider="ollama",
                model=self.model,
                prompt_length=len(prompt),
                response_length=0,
                process_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error=error_msg
            )
            return "", False, error_msg
    
    def test_connection(self) -> bool:
        """Test Ollama connection"""
        try:
            # Test with a simple prompt
            test_url = self.api_url.replace("/api/generate", "/api/tags")
            response = requests.get(test_url, timeout=10)
            return response.status_code == 200
        except:
            return False

class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not self.api_url:
            self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_response(self, prompt: str) -> Tuple[str, bool, Optional[str]]:
        """Generate response using OpenAI"""
        start_time = time.time()
        
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            process_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
                
                log_llm_interaction(
                    provider="openai",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=len(llm_response),
                    process_time_ms=process_time_ms,
                    success=True
                )
                
                return llm_response, True, None
            else:
                error_msg = f"OpenAI error: {response.status_code} - {response.text}"
                log_llm_interaction(
                    provider="openai",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=0,
                    process_time_ms=process_time_ms,
                    success=False,
                    error=error_msg
                )
                return "", False, error_msg
                
        except Exception as e:
            error_msg = f"OpenAI error: {str(e)}"
            log_llm_interaction(
                provider="openai",
                model=self.model,
                prompt_length=len(prompt),
                response_length=0,
                process_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error=error_msg
            )
            return "", False, error_msg
    
    def test_connection(self) -> bool:
        """Test OpenAI connection"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

class GeminiProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not self.api_url:
            self.api_url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent"
    
    def generate_response(self, prompt: str) -> Tuple[str, bool, Optional[str]]:
        """Generate response using Gemini"""
        start_time = time.time()
        
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            url = f"{self.api_url}?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            process_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["candidates"][0]["content"]["parts"][0]["text"]
                
                log_llm_interaction(
                    provider="gemini",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=len(llm_response),
                    process_time_ms=process_time_ms,
                    success=True
                )
                
                return llm_response, True, None
            else:
                error_msg = f"Gemini error: {response.status_code} - {response.text}"
                log_llm_interaction(
                    provider="gemini",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=0,
                    process_time_ms=process_time_ms,
                    success=False,
                    error=error_msg
                )
                return "", False, error_msg
                
        except Exception as e:
            error_msg = f"Gemini error: {str(e)}"
            log_llm_interaction(
                provider="gemini",
                model=self.model,
                prompt_length=len(prompt),
                response_length=0,
                process_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error=error_msg
            )
            return "", False, error_msg
    
    def test_connection(self) -> bool:
        """Test Gemini connection"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models?key={self.api_key}"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False

class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Azure requires specific URL format
        if not self.api_url.endswith("/chat/completions"):
            self.api_url = f"{self.api_url}/openai/deployments/{self.model}/chat/completions?api-version=2023-12-01-preview"
    
    def generate_response(self, prompt: str) -> Tuple[str, bool, Optional[str]]:
        """Generate response using Azure OpenAI"""
        start_time = time.time()
        
        try:
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            process_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
                
                log_llm_interaction(
                    provider="azure",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=len(llm_response),
                    process_time_ms=process_time_ms,
                    success=True
                )
                
                return llm_response, True, None
            else:
                error_msg = f"Azure OpenAI error: {response.status_code} - {response.text}"
                log_llm_interaction(
                    provider="azure",
                    model=self.model,
                    prompt_length=len(prompt),
                    response_length=0,
                    process_time_ms=process_time_ms,
                    success=False,
                    error=error_msg
                )
                return "", False, error_msg
                
        except Exception as e:
            error_msg = f"Azure OpenAI error: {str(e)}"
            log_llm_interaction(
                provider="azure",
                model=self.model,
                prompt_length=len(prompt),
                response_length=0,
                process_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error=error_msg
            )
            return "", False, error_msg
    
    def test_connection(self) -> bool:
        """Test Azure OpenAI connection"""
        try:
            # Simple test request
            test_payload = {
                "messages": [{"role": "user", "content": "hello"}],
                "max_tokens": 5
            }
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key
            }
            response = requests.post(
                self.api_url,
                json=test_payload,
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

class LLMManager:
    """LLM manager for handling different providers"""
    
    def __init__(self):
        self.provider: Optional[LLMProvider] = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the appropriate LLM provider"""
        try:
            config = get_llm_config()
            provider_name = config.get("provider", "ollama").lower()
            
            if provider_name == "ollama":
                self.provider = OllamaProvider(config)
            elif provider_name == "openai":
                self.provider = OpenAIProvider(config)
            elif provider_name == "gemini":
                self.provider = GeminiProvider(config)
            elif provider_name == "azure":
                self.provider = AzureOpenAIProvider(config)
            else:
                logger.error(f"Unknown LLM provider: {provider_name}")
                self.provider = OllamaProvider(config)  # Fallback to Ollama
            
            logger.info(f"Initialized LLM provider: {provider_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            # Fallback to default Ollama configuration
            self.provider = OllamaProvider({
                "provider": "ollama",
                "model": "mistral",
                "api_url": "http://localhost:11434/api/generate",
                "timeout": 60
            })
    
    def generate_response(self, prompt: str) -> Tuple[str, bool, Optional[str], str, str]:
        """Generate response from LLM. Returns (response, success, error, provider, model)"""
        if not self.provider:
            return "", False, "LLM provider not initialized", "unknown", "unknown"
        
        response, success, error = self.provider.generate_response(prompt)
        return response, success, error, self.provider.provider, self.provider.model
    
    def test_connection(self) -> bool:
        """Test LLM connection"""
        if not self.provider:
            return False
        return self.provider.test_connection()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider"""
        if not self.provider:
            return {"provider": "none", "model": "none", "status": "unavailable"}
        
        return {
            "provider": self.provider.provider,
            "model": self.provider.model,
            "api_url": self.provider.api_url,
            "status": "available" if self.test_connection() else "unavailable"
        }

# Global LLM manager instance
llm_manager = LLMManager()

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance"""
    return llm_manager

def generate_llm_response(prompt: str) -> Tuple[str, bool, Optional[str], str, str]:
    """Convenience function to generate LLM response"""
    return llm_manager.generate_response(prompt)

def test_llm_connection() -> bool:
    """Convenience function to test LLM connection"""
    return llm_manager.test_connection()

def get_llm_info() -> Dict[str, Any]:
    """Convenience function to get LLM info"""
    return llm_manager.get_provider_info()

# Legacy function names for compatibility
def query_llm(prompt: str) -> Tuple[str, bool, Optional[str], str, str]:
    """Legacy function name for generate_llm_response"""
    return generate_llm_response(prompt)

def is_llm_available() -> bool:
    """Legacy function name for test_llm_connection"""
    return test_llm_connection()