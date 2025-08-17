# 🐦 Wag-Tail AI Gateway - Open Source Edition v4.1.0

**Production-ready AI Gateway with enterprise-grade security features - 100% Open Source**

[![Version](https://img.shields.io/badge/version-4.1.0%20OSS-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-50%2F50%20passing-brightgreen.svg)]()

---

## 🌟 What is Wag-Tail?

Wag-Tail is a **secure AI gateway** that sits between your applications and Large Language Model (LLM) providers. It provides enterprise-grade security, monitoring, and routing capabilities while remaining **100% open source**.

## 🚀 Quick Navigation

| Section | Description | Quick Link |
|---------|-------------|------------|
| **🔧 Installation** | Get up and running in 5 minutes | [Install Guide](Installation-Guide) |
| **⚙️ Configuration** | Configure LLM providers and security | [Configuration](Configuration) |
| **🔌 API Reference** | Complete API documentation | [API-Reference](API-Reference) |
| **🛡️ Security** | Security features and best practices | [Security-Features](Security-Features) |
| **🧩 Plugins** | Extend with custom functionality | [Plugin-Development](Plugin-Development) |
| **🚀 Deployment** | Production deployment guide | [Deployment](Deployment) |
| **❓ FAQ** | Common questions and troubleshooting | [FAQ-&-Troubleshooting](FAQ-&-Troubleshooting) |

## 🛡️ Core Security Features

- **🔐 Multi-layer Security Pipeline**: Regex filtering, code detection, PII protection
- **🛡️ PII Detection & Masking**: Full Microsoft Presidio integration with 15+ data types
- **💻 Code Injection Prevention**: Multi-language detection (SQL, Python, JavaScript, etc.)
- **🔍 Input Validation**: JSON Schema validation with Pydantic v2
- **📝 Comprehensive Logging**: Request/response audit trails with sensitive data masking

## 🤖 Supported LLM Providers

- **Ollama** (Local LLMs) - *Recommended for privacy*
- **OpenAI** (GPT-3.5, GPT-4, o1 models)
- **Google Gemini** (Gemini 2.0 Flash)
- **Azure OpenAI**
- **Custom providers** via configuration

## ⚡ Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/startoken-wag-tail/wag-tail-ai-gateway.git
cd wag-tail-ai-gateway
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the gateway
uvicorn main:app --reload

# 4. Test it works!
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?"}'
```

## 📊 Test Results

**Latest Test Run (v4.1.0)**: 50/50 tests passing (100% success rate)
- ✅ Core Functionality: 5/5
- ✅ Security Features: 16/16  
- ✅ LLM Integration: 9/9
- ✅ Configuration: 7/7
- ✅ Performance: 4/4
- ✅ OSS Edition: Full compatibility

## 🚀 Why Choose Wag-Tail?

### vs. Commercial Solutions
- **Cost**: $0/month vs $500-2000/month
- **Privacy**: Your data stays on your infrastructure
- **Customization**: Full source code access
- **No vendor lock-in**: Use any LLM provider

### Production Ready
- **⚡ Fast**: Built on FastAPI for high performance
- **🔒 Secure**: Enterprise-grade security pipeline
- **📊 Tested**: Comprehensive test suite
- **📖 Documented**: Complete guides and API docs

## 💬 Community & Support

- **💬 Discussions**: [GitHub Discussions](../../discussions)
- **🐛 Bug Reports**: [GitHub Issues](../../issues)
- **📧 Contact**: For enterprise support and consulting

---

**🚀 Ready to secure your AI applications? Check out the [Installation Guide](Installation-Guide) to get started!**