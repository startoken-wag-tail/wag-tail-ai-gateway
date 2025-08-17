# 🔌 API Reference - v4.1.0 OSS Edition

Complete API documentation for Wag-Tail AI Gateway v4.1.0 OSS Edition.

## 📡 Base URL

```
http://localhost:8000
```

## 🔐 Authentication

All API endpoints require authentication via API key header:

```http
X-API-Key: your-api-key-here
```

## 📋 Endpoints Overview

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/health` | GET | System health check | ❌ None |
| `/chat` | POST | Main chat interface | ✅ Required |
| `/docs` | GET | Interactive API docs | ❌ None |
| `/redoc` | GET | Alternative API docs | ❌ None |

## 🏥 Health Check

### `GET /health`

System health and status information.

**Request:**
```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "4.1.0",
  "edition": "oss",
  "uptime_seconds": 3600,
  "llm_status": "available",
  "plugins_loaded": 3,
  "error": null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `healthy` or `unhealthy` |
| `version` | string | Current version |
| `edition` | string | `oss` for Open Source |
| `uptime_seconds` | integer | Seconds since startup |
| `llm_status` | string | `available` or `unavailable` |
| `plugins_loaded` | integer | Number of loaded plugins |
| `error` | string | Error message if unhealthy |

## 💬 Chat Interface

### `POST /chat`

Main chat endpoint for LLM interactions.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is artificial intelligence?"}'
```

**Request Headers:**

| Header | Required | Description | Example |
|--------|----------|-------------|---------|
| `X-API-Key` | ✅ Yes | Authentication key | `demo-key-for-testing` |
| `Content-Type` | ✅ Yes | Must be `application/json` | `application/json` |
| `X-LLM-Provider` | ❌ Optional | Override LLM provider | `openai`, `ollama`, `gemini` |
| `X-LLM-Model` | ❌ Optional | Override LLM model | `gpt-4`, `mistral` |
| `X-Group-ID` | ❌ Optional | Group identifier | `development`, `production` |

**Request Body:**
```json
{
  "prompt": "Your question or instruction here"
}
```

**Request Schema:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `prompt` | string | ✅ Yes | 1-10000 chars | User input to process |

**Success Response (200):**
```json
{
  "response": "Artificial intelligence (AI) refers to...",
  "flag": "safe",
  "llm_provider": "ollama",
  "llm_model_name": "mistral",
  "cache_hit": false,
  "process_time_ms": 1234,
  "pii_detected": false,
  "pii_types": []
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | LLM response text |
| `flag` | string | `safe`, `blocked`, `error` |
| `llm_provider` | string | LLM provider used |
| `llm_model_name` | string | Model used |
| `cache_hit` | boolean | Whether response was cached |
| `process_time_ms` | integer | Processing time in milliseconds |
| `pii_detected` | boolean | Whether PII was detected |
| `pii_types` | array | Types of PII found (if any) |

## 🛡️ Security Responses

### Blocked Request (Security Filter)

**Request with SQL Injection:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "DROP TABLE users; --"}'
```

**Response (200):**
```json
{
  "response": "",
  "flag": "blocked",
  "reason": "SQL injection pattern detected",
  "llm_provider": "security_filter",
  "llm_model_name": "basic_guard",
  "cache_hit": false,
  "process_time_ms": 15,
  "pii_detected": false
}
```

### PII Detection Response

**Request with PII:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My email is john@example.com"}'
```

**Response (200):**
```json
{
  "response": "",
  "flag": "blocked",
  "reason": "High-confidence PII detected: EMAIL_ADDRESS",
  "llm_provider": "pii_guard",
  "llm_model_name": "presidio",
  "cache_hit": false,
  "process_time_ms": 25,
  "pii_detected": true,
  "pii_types": ["EMAIL_ADDRESS"]
}
```

## 🎛️ Header-Based Model Selection

Override the default LLM provider and model using headers:

**OpenAI Override:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "X-LLM-Provider: openai" \
  -H "X-LLM-Model: gpt-4" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing"}'
```

**Supported Provider/Model Combinations:**

| Provider | Models | Example |
|----------|--------|---------|
| `openai` | `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo` | `X-LLM-Provider: openai` |
| `ollama` | `mistral`, `llama2`, `codellama` | `X-LLM-Provider: ollama` |
| `gemini` | `gemini-pro`, `gemini-2.0-flash` | `X-LLM-Provider: gemini` |
| `azure` | Your deployment names | `X-LLM-Provider: azure` |

## ❌ Error Responses

### Authentication Error (401)

**Missing or invalid API key:**
```json
{
  "response": "",
  "flag": "blocked",
  "reason": "Invalid API key",
  "llm_provider": "auth_filter",
  "llm_model_name": "simple_auth",
  "cache_hit": false,
  "process_time_ms": 5
}
```

### Validation Error (422)

**Invalid request format:**
```json
{
  "detail": [
    {
      "loc": ["body", "prompt"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### LLM Provider Error

**LLM service unavailable:**
```json
{
  "response": "",
  "flag": "llm_error",
  "reason": "LLM processing failed",
  "llm_provider": "ollama",
  "llm_model_name": "mistral",
  "cache_hit": false,
  "process_time_ms": 100
}
```

### Server Error (500)

**Internal server error:**
```json
{
  "error": "Internal server error",
  "code": "INTERNAL_ERROR",
  "details": {
    "message": "An unexpected error occurred"
  }
}
```

## 📊 Response Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | Success | Request processed successfully |
| `401` | Unauthorized | Invalid or missing API key |
| `422` | Unprocessable Entity | Invalid request format |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server-side error |
| `503` | Service Unavailable | LLM provider unavailable |

## 🔍 Request Examples

### Basic Chat Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the benefits of renewable energy"
  }'
```

### Code Generation Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "X-LLM-Provider: openai" \
  -H "X-LLM-Model: gpt-4" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to calculate fibonacci numbers"
  }'
```

### Translation Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Translate to French: Hello, how are you today?"
  }'
```

### Creative Writing Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "X-LLM-Provider: ollama" \
  -H "X-LLM-Model: mistral" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a short story about a robot learning to paint"
  }'
```

## 🐍 Python SDK Example

```python
import requests
import json

class WagTailClient:
    def __init__(self, base_url="http://localhost:8000", api_key="demo-key-for-testing"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def chat(self, prompt, provider=None, model=None):
        """Send a chat request to Wag-Tail Gateway"""
        headers = self.headers.copy()
        
        if provider:
            headers["X-LLM-Provider"] = provider
        if model:
            headers["X-LLM-Model"] = model
        
        response = requests.post(
            f"{self.base_url}/chat",
            headers=headers,
            json={"prompt": prompt}
        )
        
        return response.json()
    
    def health(self):
        """Check system health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage example
client = WagTailClient()

# Basic chat
result = client.chat("What is machine learning?")
print(result["response"])

# With specific provider
result = client.chat(
    "Explain quantum computing", 
    provider="openai", 
    model="gpt-4"
)
print(result["response"])

# Health check
health = client.health()
print(f"System status: {health['status']}")
```

## 🔧 JavaScript/Node.js Example

```javascript
class WagTailClient {
    constructor(baseUrl = 'http://localhost:8000', apiKey = 'demo-key-for-testing') {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async chat(prompt, options = {}) {
        const headers = {
            'X-API-Key': this.apiKey,
            'Content-Type': 'application/json'
        };
        
        if (options.provider) headers['X-LLM-Provider'] = options.provider;
        if (options.model) headers['X-LLM-Model'] = options.model;
        
        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ prompt })
        });
        
        return await response.json();
    }
    
    async health() {
        const response = await fetch(`${this.baseUrl}/health`);
        return await response.json();
    }
}

// Usage example
const client = new WagTailClient();

// Basic chat
client.chat('Explain blockchain technology')
    .then(result => console.log(result.response));

// With specific provider
client.chat('Write a poem about AI', { 
    provider: 'openai', 
    model: 'gpt-4' 
}).then(result => console.log(result.response));
```

## 📚 Interactive Documentation

Wag-Tail provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- ✅ Test API endpoints directly
- ✅ View request/response schemas
- ✅ See authentication requirements
- ✅ Download OpenAPI specifications

## 🔄 Rate Limiting

The OSS edition includes basic rate limiting:

- **Default**: 60 requests per minute per API key
- **Headers**: Rate limit info in response headers
- **Exceeded**: Returns 429 status code

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## 📞 Getting Help

- **📚 Next Steps**: [Security Features](Security-Features)
- **🧩 Plugins**: [Plugin Development](Plugin-Development)
- **💬 Community**: [GitHub Discussions](../../discussions)
- **🐛 API Issues**: [Report API Issues](../../issues)

---

**🔌 API Reference complete! Start building with Wag-Tail AI Gateway v4.1.0 OSS Edition's secure and powerful API.**