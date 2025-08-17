# 🧩 Plugin Development - v4.1.0 OSS Edition

Learn how to extend Wag-Tail AI Gateway v4.1.0 OSS Edition with custom plugins using the StarToken plugin framework.

## 🏗️ Plugin Architecture Overview

Wag-Tail uses the **StarToken plugin framework** to provide a modular, extensible architecture:

```
📥 Request → 🔌 Plugin Chain → 🤖 LLM → 🔌 Response Plugins → 📤 Response
```

### Plugin Types

| Plugin Type | Purpose | Execution Point | Examples |
|-------------|---------|-----------------|----------|
| **Authentication** | Validate API keys | Before processing | `wag_tail_key_auth` |
| **Security Guard** | Filter malicious content | Before LLM | `wag_tail_basic_guard` |
| **PII Protection** | Detect personal data | Before LLM | `wag_tail_pii_guard` |
| **Response Filter** | Process LLM output | After LLM | Custom output filters |
| **Webhook** | External integrations | Configurable | `wag_tail_webhook_guardrail` |

## 🚀 Quick Start: Your First Plugin

### 1. Plugin Structure

```
your_plugin/
├── __init__.py
├── your_plugin.py
└── plugin.yaml
```

### 2. Basic Plugin Template

**`your_plugin/your_plugin.py`:**
```python
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class YourCustomPlugin:
    """
    Custom plugin for Wag-Tail AI Gateway
    """
    
    def __init__(self):
        self.name = "your_custom_plugin"
        self.version = "1.0.0"
        self.description = "Your custom plugin description"
        logger.info(f"Initialized {self.name} v{self.version}")
    
    def on_request(self, request, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming requests before they reach the LLM
        
        Args:
            request: FastAPI request object
            context: Request context dictionary
            
        Returns:
            None: Continue processing
            Dict: Block request with this response
        """
        prompt = context.get("prompt", "")
        
        # Your custom logic here
        if self.should_block_request(prompt):
            return {
                "blocked": True,
                "reason": "Custom security rule triggered",
                "confidence": 0.9
            }
        
        # Allow request to continue
        return None
    
    def on_response(self, request, context: Dict[str, Any], response: str) -> Tuple[str, bool]:
        """
        Process LLM responses before returning to client
        
        Args:
            request: FastAPI request object
            context: Request context dictionary
            response: LLM response text
            
        Returns:
            Tuple[str, bool]: (modified_response, was_modified)
        """
        # Your response processing logic here
        modified_response = self.process_response(response)
        was_modified = modified_response != response
        
        return modified_response, was_modified
    
    def should_block_request(self, prompt: str) -> bool:
        """Custom logic to determine if request should be blocked"""
        # Example: Block requests containing "forbidden_word"
        forbidden_words = ["forbidden_word", "blocked_term"]
        return any(word in prompt.lower() for word in forbidden_words)
    
    def process_response(self, response: str) -> str:
        """Custom logic to process LLM responses"""
        # Example: Add a disclaimer to all responses
        disclaimer = "\n\n(This response was processed by YourCustomPlugin)"
        return response + disclaimer
```

**`your_plugin/__init__.py`:**
```python
from .your_plugin import YourCustomPlugin

# Plugin entry point
def create_plugin():
    return YourCustomPlugin()
```

**`your_plugin/plugin.yaml`:**
```yaml
name: "your_custom_plugin"
version: "1.0.0"
description: "Your custom plugin for Wag-Tail AI Gateway v4.1.0 OSS Edition"
author: "Your Name"
license: "Apache-2.0"

# Plugin configuration
enabled: true
priority: 100  # Lower numbers = higher priority

# Dependencies (optional)
dependencies:
  - "requests>=2.25.0"
  - "pydantic>=1.8.0"

# Plugin-specific configuration
config:
  forbidden_words:
    - "forbidden_word"
    - "blocked_term"
  add_disclaimer: true
  disclaimer_text: "This response was processed by YourCustomPlugin"
```

## 🔧 Plugin Installation

### Method 1: Add to StarToken Plugins Directory

```bash
# 1. Create plugin directory
mkdir startoken-plugins/your_custom_plugin

# 2. Copy your plugin files
cp -r your_plugin/* startoken-plugins/your_custom_plugin/

# 3. Restart Wag-Tail
uvicorn main:app --reload
```

### Method 2: Development Installation

```bash
# 1. Create plugin in development directory
mkdir -p plugins/your_custom_plugin
cd plugins/your_custom_plugin

# 2. Create plugin files (as shown above)

# 3. Register plugin in plugin_loader.py
# Add your plugin to the AVAILABLE_PLUGINS list
```

## 📚 Plugin API Reference

### Core Plugin Methods

#### `on_request(request, context) -> Optional[Dict]`

**Purpose**: Process incoming requests before LLM processing

**Parameters:**
- `request`: FastAPI Request object
- `context`: Dictionary containing:
  - `prompt`: User input
  - `api_key`: API key (masked)
  - `client_ip`: Client IP address
  - `timestamp`: Request timestamp
  - `edition`: "oss" or "advanced"

**Return Values:**
- `None`: Continue processing
- `Dict` with `blocked: True`: Block request

**Example:**
```python
def on_request(self, request, context):
    prompt = context.get("prompt", "")
    
    # Block empty prompts
    if not prompt.strip():
        return {
            "blocked": True,
            "reason": "Empty prompt not allowed",
            "confidence": 1.0
        }
    
    return None  # Continue processing
```

#### `on_response(request, context, response) -> Tuple[str, bool]`

**Purpose**: Process LLM responses before returning to client

**Parameters:**
- `request`: FastAPI Request object  
- `context`: Request context dictionary
- `response`: LLM response text

**Return Values:**
- `Tuple[str, bool]`: (modified_response, was_modified)

**Example:**
```python
def on_response(self, request, context, response):
    # Add word count to response
    word_count = len(response.split())
    modified = f"{response}\n\n[Word count: {word_count}]"
    
    return modified, True  # Response was modified
```

### Context Dictionary

**Available Context Fields:**
```python
context = {
    "request": request,           # FastAPI Request object
    "prompt": "user input",       # User's prompt
    "api_key": "demo-key...",     # API key (original)
    "masked_api_key": "****123",  # Masked API key for logging
    "client_ip": "192.168.1.1",  # Client IP address
    "timestamp": 1642684800.0,    # Unix timestamp
    "edition": "oss",             # Edition (oss/advanced)
    "plugins": [...],             # List of loaded plugins
    
    # Optional fields (may be added by other plugins)
    "group_id": "production",     # Group identifier
    "user_id": "user123",         # User identifier
    "session_id": "sess_abc",     # Session identifier
}
```

## 🛡️ Security Plugin Examples

### Content Filter Plugin

```python
import re
from typing import Optional, Dict, Any

class ContentFilterPlugin:
    def __init__(self):
        self.name = "content_filter"
        self.blocked_patterns = [
            r"(?i)\b(spam|scam|phishing)\b",
            r"(?i)\b(hack|crack|exploit)\b",
            r"(?i)\b(illegal|stolen|pirated)\b"
        ]
    
    def on_request(self, request, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        prompt = context.get("prompt", "")
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, prompt):
                return {
                    "blocked": True,
                    "reason": f"Content policy violation: {pattern}",
                    "confidence": 0.9
                }
        
        return None
```

### Rate Limiting Plugin

```python
import time
from collections import defaultdict
from typing import Optional, Dict, Any

class RateLimitPlugin:
    def __init__(self):
        self.name = "rate_limit"
        self.requests = defaultdict(list)
        self.max_requests = 10  # per minute
        self.window = 60  # seconds
    
    def on_request(self, request, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        api_key = context.get("api_key", "")
        now = time.time()
        
        # Clean old requests
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if now - req_time < self.window
        ]
        
        # Check rate limit
        if len(self.requests[api_key]) >= self.max_requests:
            return {
                "blocked": True,
                "reason": "Rate limit exceeded",
                "confidence": 1.0
            }
        
        # Record this request
        self.requests[api_key].append(now)
        return None
```

### Custom PII Plugin

```python
import re
from typing import Optional, Dict, Any, Tuple

class CustomPIIPlugin:
    def __init__(self):
        self.name = "custom_pii"
        self.patterns = {
            "employee_id": r"\b[E][0-9]{6}\b",
            "project_code": r"\b[P][0-9]{4}-[A-Z]{2}\b",
            "internal_ip": r"\b10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b"
        }
    
    def on_request(self, request, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        prompt = context.get("prompt", "")
        
        for pii_type, pattern in self.patterns.items():
            if re.search(pattern, prompt):
                return {
                    "blocked": True,
                    "reason": f"Custom PII detected: {pii_type}",
                    "confidence": 0.95
                }
        
        return None
    
    def on_response(self, request, context: Dict[str, Any], response: str) -> Tuple[str, bool]:
        """Mask any PII in responses"""
        modified = response
        was_modified = False
        
        for pii_type, pattern in self.patterns.items():
            if re.search(pattern, modified):
                modified = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", modified)
                was_modified = True
        
        return modified, was_modified
```

## 🔌 Advanced Plugin Features

### Plugin Configuration

**Access plugin configuration:**
```python
class ConfigurablePlugin:
    def __init__(self, config: Dict[str, Any] = None):
        self.name = "configurable_plugin"
        self.config = config or {}
        
        # Get configuration values
        self.max_length = self.config.get("max_length", 1000)
        self.blocked_words = self.config.get("blocked_words", [])
        self.log_level = self.config.get("log_level", "INFO")
```

**Plugin configuration in YAML:**
```yaml
# config/sys_config.yaml
plugins:
  configurable_plugin:
    enabled: true
    config:
      max_length: 2000
      blocked_words: ["spam", "fake"]
      log_level: "DEBUG"
```

### Stateful Plugins

**Plugins with persistent state:**
```python
import json
import os
from typing import Dict, Any

class StatefulPlugin:
    def __init__(self):
        self.name = "stateful_plugin"
        self.state_file = "plugin_state.json"
        self.state = self.load_state()
    
    def load_state(self) -> Dict[str, Any]:
        """Load plugin state from file"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {"request_count": 0, "blocked_count": 0}
    
    def save_state(self):
        """Save plugin state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)
    
    def on_request(self, request, context: Dict[str, Any]):
        self.state["request_count"] += 1
        
        # Your logic here
        if self.should_block(context):
            self.state["blocked_count"] += 1
            self.save_state()
            return {"blocked": True, "reason": "Stateful blocking"}
        
        self.save_state()
        return None
```

### Plugin Dependencies

**Plugin with external dependencies:**
```python
# your_plugin/requirements.txt
requests>=2.25.0
beautifulsoup4>=4.9.0
pandas>=1.3.0

# your_plugin/your_plugin.py
try:
    import requests
    import pandas as pd
    from bs4 import BeautifulSoup
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    import logging
    logging.warning(f"Plugin dependencies not available: {e}")

class DependencyPlugin:
    def __init__(self):
        self.name = "dependency_plugin"
        self.enabled = DEPENDENCIES_AVAILABLE
        
        if not self.enabled:
            logging.warning(f"{self.name} disabled due to missing dependencies")
```

## 🧪 Plugin Testing

### Test Framework

```python
import unittest
from unittest.mock import Mock
from your_plugin import YourCustomPlugin

class TestYourPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = YourCustomPlugin()
    
    def test_blocks_forbidden_content(self):
        """Test that forbidden content is blocked"""
        request = Mock()
        context = {
            "prompt": "This contains forbidden_word in it",
            "api_key": "test-key"
        }
        
        result = self.plugin.on_request(request, context)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.get("blocked"))
        self.assertIn("Custom security rule", result.get("reason", ""))
    
    def test_allows_safe_content(self):
        """Test that safe content is allowed"""
        request = Mock()
        context = {
            "prompt": "This is a safe prompt",
            "api_key": "test-key"
        }
        
        result = self.plugin.on_request(request, context)
        self.assertIsNone(result)
    
    def test_response_modification(self):
        """Test response modification"""
        request = Mock()
        context = {"api_key": "test-key"}
        response = "Original response"
        
        modified, was_modified = self.plugin.on_response(request, context, response)
        
        self.assertTrue(was_modified)
        self.assertIn("YourCustomPlugin", modified)

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing

```python
# test_plugin_integration.py
import requests

def test_plugin_integration():
    """Test plugin integration with Wag-Tail"""
    
    # Test blocked content
    response = requests.post(
        "http://localhost:8000/chat",
        headers={"X-API-Key": "demo-key-for-testing"},
        json={"prompt": "forbidden_word test"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["flag"] == "blocked"
    assert "Custom security rule" in data["reason"]
    
    # Test allowed content
    response = requests.post(
        "http://localhost:8000/chat",
        headers={"X-API-Key": "demo-key-for-testing"},
        json={"prompt": "safe content"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["flag"] == "safe"
    assert "YourCustomPlugin" in data["response"]

if __name__ == "__main__":
    test_plugin_integration()
    print("✅ Plugin integration tests passed!")
```

## 📦 Plugin Distribution

### Plugin Package Structure

```
your_plugin_package/
├── setup.py
├── README.md
├── requirements.txt
├── your_plugin/
│   ├── __init__.py
│   ├── your_plugin.py
│   └── plugin.yaml
├── tests/
│   └── test_your_plugin.py
└── examples/
    └── example_usage.py
```

### Setup.py for Distribution

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="wag-tail-your-plugin",
    version="1.0.0",
    description="Your custom plugin for Wag-Tail AI Gateway",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=1.8.0"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
)
```

## 🔍 Plugin Debugging

### Debugging Tips

**Add comprehensive logging:**
```python
import logging

logger = logging.getLogger(__name__)

class DebuggablePlugin:
    def on_request(self, request, context):
        logger.debug(f"Processing request: {context.get('masked_api_key')}")
        logger.debug(f"Prompt length: {len(context.get('prompt', ''))}")
        
        # Your logic here
        result = self.process_request(context)
        
        if result:
            logger.warning(f"Request blocked: {result.get('reason')}")
        else:
            logger.debug("Request allowed")
        
        return result
```

**Use debug mode:**
```yaml
# config/environments/development.yaml
logging:
  level: "DEBUG"
  
plugins:
  your_plugin:
    enabled: true
    config:
      debug_mode: true
```

**Monitor plugin performance:**
```python
import time

class PerformancePlugin:
    def on_request(self, request, context):
        start_time = time.time()
        
        # Your processing logic
        result = self.process_request(context)
        
        processing_time = time.time() - start_time
        logger.info(f"Plugin processing time: {processing_time:.3f}s")
        
        return result
```

## 📞 Getting Help

- **📚 Next Steps**: [Deployment Guide](Deployment)
- **🔧 API Reference**: [API Reference](API-Reference)
- **💬 Plugin Development**: [GitHub Discussions](../../discussions)
- **🐛 Plugin Issues**: [Report Plugin Issues](../../issues)
- **🧩 Plugin Examples**: [StarToken Plugins Repository](../startoken-plugins/)

---

**🧩 Plugin Development complete! You're now ready to extend Wag-Tail AI Gateway v4.1.0 OSS Edition with custom functionality.**