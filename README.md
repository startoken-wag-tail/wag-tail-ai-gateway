# 🐦 Wag-Tail AI Gateway - Open Source Edition

**Production-ready AI Gateway with enterprise-grade security features - 100% Open Source**

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-red.svg)](https://pydantic.dev)

---

## 🌟 What's Included in Open Source Edition

### 🛡️ **Enterprise-Grade Security - Free Forever**
- **🔐 Multi-layer Security Pipeline**: Regex filtering, code detection, PII protection
- **🛡️ PII Detection & Masking**: Full Microsoft Presidio integration with 15+ data types
- **💻 Code Injection Prevention**: Multi-language detection (SQL, Python, JavaScript, etc.)
- **🔍 Input Validation**: JSON Schema validation with Pydantic v2
- **📝 Comprehensive Logging**: Request/response audit trails with sensitive data masking

### 🚀 **Production-Ready Features**
- **⚡ Fast API Gateway**: Built on FastAPI for high performance
- **🎛️ Header-Based Routing**: Override LLM models via X-LLM-Provider headers
- **📊 Health Monitoring**: System health checks and status endpoints
- **🐳 Container Ready**: Easy deployment with Docker (coming soon)

### 🤖 **LLM Provider Support**
- **Ollama** (Local LLMs) - *Recommended for privacy*
- **OpenAI** (GPT-3.5, GPT-4)
- **Google Gemini** 
- **Azure OpenAI**
- **Custom providers** via configuration

---

## 📋 Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+** (Required for API key management and usage tracking)

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Clone and setup
git clone https://github.com/startoken-wag-tail/wag-tail-ai-gateway.git
cd wag-tail-ai-gateway
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Setup PostgreSQL database (optional - for API key management)
# Create database and tables:
psql -U postgres -c "CREATE DATABASE wag_tail;"
psql -U postgres -d wag_tail -f database/schema.sql

# 4. Start the gateway
uvicorn main:app --reload

# 5. Test it works!
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?"}'
```

**✅ That's it! Your secure AI gateway is running with full PII protection.**

---

## 🔧 Configuration

### Basic Configuration
```yaml
# config/sys_config.yaml
llm:
  provider: "ollama"  # ollama, openai, gemini, azure
  model: "mistral"
  api_url: "http://localhost:11434/api/generate"
  api_key: ""  # Leave empty for Ollama

security:
  enable_pii_detection: true
  enable_code_detection: true
  max_prompt_length: 10000

logging:
  level: "INFO"
  file: "logs/wag_tail_gateway.log"
  max_size_mb: 50
```

### Environment Variables
```bash
# Optional: Set via environment variables
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export AZURE_OPENAI_API_KEY="your-azure-key"
```

---

## 🛡️ Security Features

### 1. **PII Detection & Protection** 
Automatically detects and masks:
- **Email addresses** → `****@***.com`
- **Phone numbers** → `***-***-****`
- **Social Security Numbers** → `***-**-****`
- **Credit card numbers** → `****-****-****-****`
- **Custom patterns** (configurable)

```bash
# Test PII detection
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My email is john@example.com"}'

# Response: PII detected and blocked
{
  "response": "",
  "flag": "blocked", 
  "reason": "PII detected: EMAIL_ADDRESS"
}
```

### 2. **Code Injection Prevention**
Detects and blocks code in multiple languages:
- **SQL injection** → `SELECT * FROM users`
- **Python code** → `import os; os.system(...)`
- **JavaScript** → `<script>alert('xss')</script>`
- **Command injection** → `; rm -rf /`

### 3. **Input Validation**
- **JSON Schema validation** with Pydantic v2
- **Request size limits** (configurable)
- **Rate limiting** support
- **API key authentication**

---

## 📡 API Reference

### Chat Endpoint
```bash
POST /chat
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json
  # Optional model overrides:
  X-LLM-Provider: openai
  X-LLM-Model: gpt-4

Body:
{
  "prompt": "Your question here"
}
```

### Response Format
```json
{
  "response": "AI response text",
  "flag": "safe",
  "llm_provider": "ollama", 
  "llm_model_name": "mistral",
  "cache_hit": false,
  "process_time_ms": 1234,
  "pii_detected": false
}
```

### Health Check
```bash
GET /health
# Returns system status
{
  "status": "healthy",
  "version": "1.0.0",
  "edition": "oss",
  "uptime_seconds": 3600
}
```

---

## 🔧 Installation & Setup

### Prerequisites
- **Python 3.9+** 
- **2GB+ RAM** (4GB+ recommended)
- **Optional:** Docker for containerized deployment

### 1. Local LLM Setup (Recommended)
```bash
# Install Ollama for privacy-focused local LLMs
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull mistral
ollama serve  # Starts on localhost:11434
```

### 2. Cloud LLM Setup (Optional)
```bash
# For OpenAI
export OPENAI_API_KEY="sk-your-key-here"

# Update config/sys_config.yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
```

### 3. Production Deployment
```bash
# Production server with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With reverse proxy (nginx recommended)
server {
    listen 80;
    location / {
        proxy_pass http://localhost:8000;
        proxy_read_timeout 300s;  # For longer LLM responses
    }
}
```

---

## 🧪 Testing & Validation

### Security Tests
```bash
# Test PII protection
python test_pii_protection.py

# Test SQL injection blocking  
python test_security_filters.py

# Test code detection
python test_code_detection.py
```

### Performance Tests
```bash
# Load testing
python test_performance.py

# Health checks
curl http://localhost:8000/health
```

---

## 🔍 Monitoring & Observability

### Log Analysis
```bash
# Monitor real-time logs
tail -f logs/wag_tail_gateway.log

# Check for security events
grep -i "blocked\|pii\|injection" logs/wag_tail_gateway.log

# Performance metrics
grep "process_time_ms" logs/wag_tail_gateway.log | tail -10
```

### Metrics Available
- **Request/response times**
- **Security block events**
- **PII detection counts**
- **LLM provider performance**
- **Error rates and types**

---

## 🚀 Why Choose Wag-Tail OSS?

### vs. Other Open Source AI Gateways
| Feature | Wag-Tail OSS | Competitor A | Competitor B |
|---------|:------------:|:------------:|:------------:|
| **PII Detection** | ✅ Full Presidio | ❌ None | ❌ Basic regex |
| **Code Detection** | ✅ 15+ languages | ❌ None | ❌ SQL only |
| **JSON Validation** | ✅ Pydantic v2 | ❌ Manual | ❌ None |
| **Webhook Support** | ✅ HMAC signed | ❌ None | ❌ Basic HTTP |
| **Production Ready** | ✅ Yes | ❌ Beta | ❌ Alpha |
| **License** | ✅ Apache 2.0 | ✅ MIT | ❌ GPL |

### vs. Commercial Solutions
- **Cost**: $0/month vs $500-2000/month
- **Privacy**: Your data stays on your infrastructure
- **Customization**: Full source code access
- **No vendor lock-in**: Use any LLM provider

---

## 🛠️ Development & Contribution

### Plugin Development
Extend Wag-Tail with custom security rules:
```python
from plugins.base import PluginBase

class CustomSecurityPlugin(PluginBase):
    def on_request(self, request, context):
        # Your custom security logic
        if self.detect_threat(request.prompt):
            return {"blocked": True, "reason": "Custom threat detected"}
        return None
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 📞 Support & Resources

### 💬 **Join Our Community**
- **💬 Discussions**: [GitHub Discussions](../../discussions) - Ask questions, share ideas, get help
- **❓ Q&A Support**: [Q&A Category](../../discussions/categories/q-a) - Get help from the community
- **💡 Feature Requests**: [Feature Requests](../../discussions/categories/feature-requests) - Suggest improvements
- **🐛 Bug Reports**: [GitHub Issues](../../issues) - Report bugs and technical issues
- **📢 Announcements**: [Follow releases](../../releases) - Stay updated with new versions
- **📖 Documentation**: [Full docs](https://www.wag-tail.com/#docs)

### Enterprise Features
Need more? Check out **Wag-Tail Advanced Edition** for:
- **🔄 External Integrations**: Webhook support for external GuardRail systems
- **🚀 30x Performance**: Semantic caching with vector similarity
- **⚡ Priority Queues**: Enterprise customer prioritization
- **🔄 Advanced Routing**: Multi-provider fallback chains
- **📊 Full Observability**: Langfuse integration, metrics, alerting
- **🗝️ Vault Integration**: Enterprise secret management
- **📞 24/7 Support**: Dedicated engineering support

---

## 📋 License

**Apache License 2.0** - Free for commercial and personal use.

See [LICENSE](LICENSE) file for details.

---

## 🎯 Roadmap

### v1.1 (Coming Soon)
- [ ] Docker container support
- [ ] Kubernetes deployment manifests
- [ ] Web UI for configuration
- [ ] More LLM provider integrations

### v1.2 (Q2 2025)
- [ ] Plugin marketplace
- [ ] Advanced PII customization
- [ ] Performance dashboard
- [ ] Prometheus metrics export

---

**🚀 Ready to secure your AI applications? Get started in 5 minutes!**

```bash
git clone https://github.com/startoken-wag-tail/wag-tail-ai-gateway.git && cd wag-tail-ai-gateway && pip install -r requirements.txt && uvicorn main:app --reload
```
