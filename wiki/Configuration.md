# ⚙️ Configuration Guide - v4.1.0 OSS Edition

Complete guide to configuring Wag-Tail AI Gateway v4.1.0 OSS Edition for your specific needs.

## 📁 Configuration Files Overview

| File | Purpose | Environment | Required |
|------|---------|-------------|----------|
| `config/sys_config.yaml` | Main system configuration | All | ✅ Yes |
| `config/environments/development.yaml` | Development overrides | Development | Optional |
| `config/environments/staging.yaml` | Staging overrides | Staging | Optional |
| `config/environments/production.yaml` | Production overrides | Production | Optional |

## 🔧 System Configuration (`sys_config.yaml`)

### Basic Configuration Structure

```yaml
# config/sys_config.yaml
llm:
  provider: "ollama"
  model: "mistral"
  api_url: "http://localhost:11434/api/generate"
  api_key: ""
  timeout: 30
  max_retries: 3

security:
  enable_pii_detection: true
  enable_code_detection: true
  enable_regex_filtering: true
  max_prompt_length: 10000
  blocked_patterns:
    - "DROP TABLE"
    - "rm -rf"
    - "DELETE FROM"

api:
  default_api_key: "demo-key-for-testing"
  cors_origins: ["*"]
  rate_limit_per_minute: 60

logging:
  level: "INFO"
  file: "logs/wag_tail_gateway.log"
  max_size_mb: 50
  backup_count: 5
  mask_sensitive_data: true

webhook:
  enabled: false
  url: ""
  timeout: 10
  hmac_secret: ""
```

## 🤖 LLM Provider Configuration

### Ollama (Local LLMs)

```yaml
llm:
  provider: "ollama"
  model: "mistral"  # or llama2, codellama, etc.
  api_url: "http://localhost:11434/api/generate"
  api_key: ""  # Not required for Ollama
  timeout: 60
  max_retries: 3
  
  # Ollama-specific settings
  stream: false
  temperature: 0.7
  top_p: 0.9
  max_tokens: 2048
```

**Supported Ollama Models:**
- `mistral` - General purpose, fast
- `llama2` - Meta's LLaMA 2
- `codellama` - Code-focused model
- `phi` - Microsoft's small model
- `neural-chat` - Conversational model

### OpenAI

```yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"  # or gpt-4, gpt-4-turbo
  api_key: "${OPENAI_API_KEY}"
  api_url: "https://api.openai.com/v1/chat/completions"
  timeout: 30
  max_retries: 3
  
  # OpenAI-specific settings
  temperature: 0.7
  max_tokens: 2048
  top_p: 1.0
  frequency_penalty: 0.0
  presence_penalty: 0.0
```

**Supported OpenAI Models:**
- `gpt-3.5-turbo` - Fast and cost-effective
- `gpt-4` - Most capable model
- `gpt-4-turbo` - Latest GPT-4 variant
- `gpt-4o` - Optimized for speed

### Google Gemini

```yaml
llm:
  provider: "gemini"
  model: "gemini-2.0-flash"
  api_key: "${GEMINI_API_KEY}"
  api_url: "https://generativelanguage.googleapis.com/v1beta/models"
  timeout: 30
  max_retries: 3
  
  # Gemini-specific settings
  temperature: 0.7
  top_p: 0.8
  top_k: 10
  max_output_tokens: 2048
```

### Azure OpenAI

```yaml
llm:
  provider: "azure"
  model: "gpt-35-turbo"  # Your deployment name
  api_key: "${AZURE_OPENAI_API_KEY}"
  api_url: "${AZURE_OPENAI_ENDPOINT}"
  api_version: "2024-02-15-preview"
  timeout: 30
  max_retries: 3
  
  # Azure-specific settings
  temperature: 0.7
  max_tokens: 2048
```

## 🛡️ Security Configuration

### PII Detection Settings

```yaml
security:
  enable_pii_detection: true
  pii_confidence_threshold: 0.8  # 0.0 to 1.0
  pii_action: "block"  # "block", "mask", or "log"
  
  # Supported PII types
  pii_types:
    - "CREDIT_CARD"
    - "EMAIL_ADDRESS"
    - "PHONE_NUMBER"
    - "SSN"
    - "PERSON"
    - "LOCATION"
    - "DATE_TIME"
    - "IP_ADDRESS"
    - "URL"
    - "CRYPTO"
```

### Code Detection Settings

```yaml
security:
  enable_code_detection: true
  code_confidence_threshold: 0.7
  
  # Detected languages
  code_languages:
    - "sql"
    - "python"
    - "javascript"
    - "bash"
    - "powershell"
    - "php"
```

### Custom Regex Patterns

```yaml
security:
  enable_regex_filtering: true
  blocked_patterns:
    # SQL Injection
    - "(?i)(drop|delete|insert|update|create|alter)\\s+(table|database|index)"
    - "(?i)union\\s+select"
    - "(?i)or\\s+1\\s*=\\s*1"
    
    # Command Injection
    - "(?i)rm\\s+-rf"
    - "(?i)sudo\\s+rm"
    - "(?i)del\\s+/[a-z]"
    
    # Custom patterns
    - "password\\s*[:=]\\s*[\"']?\\w+[\"']?"
    - "api[_-]?key\\s*[:=]\\s*[\"']?[a-zA-Z0-9]+[\"']?"
```

## 🌍 Environment-Specific Configuration

### Development Environment

```yaml
# config/environments/development.yaml
llm:
  provider: "ollama"  # Use local models for development
  model: "mistral"
  timeout: 60  # Longer timeout for debugging

logging:
  level: "DEBUG"
  file: "logs/development.log"

security:
  enable_pii_detection: false  # Disable for faster development
  max_prompt_length: 50000  # Allow longer prompts for testing

api:
  cors_origins: ["http://localhost:3000", "http://127.0.0.1:3000"]
```

### Production Environment

```yaml
# config/environments/production.yaml
llm:
  provider: "openai"  # Use production-grade models
  model: "gpt-3.5-turbo"
  timeout: 15  # Shorter timeout for production
  max_retries: 2

logging:
  level: "WARNING"
  file: "logs/production.log"
  max_size_mb: 100

security:
  enable_pii_detection: true
  enable_code_detection: true
  pii_confidence_threshold: 0.9  # Higher confidence in production
  max_prompt_length: 5000  # Stricter limits

api:
  cors_origins: ["https://yourdomain.com"]
  rate_limit_per_minute: 30  # Lower rate limit
```

## 🔐 API Authentication

### Default API Key

```yaml
api:
  default_api_key: "your-secure-api-key-here"
  require_api_key: true
```

### Multiple API Keys (Future Feature)

```yaml
api:
  api_keys:
    - key: "dev-key-12345"
      description: "Development team"
      rate_limit: 100
    - key: "prod-key-67890"
      description: "Production app"
      rate_limit: 1000
```

## 📝 Logging Configuration

### Log Levels

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # File logging
  file: "logs/wag_tail_gateway.log"
  max_size_mb: 50
  backup_count: 5
  
  # Console logging
  console: true
  
  # Sensitive data masking
  mask_sensitive_data: true
  mask_api_keys: true
  mask_prompts: false
```

### Structured Logging

```yaml
logging:
  structured: true  # JSON format
  include_request_id: true
  include_user_agent: true
  include_ip_address: true
```

## 🔗 Webhook Configuration

```yaml
webhook:
  enabled: true
  url: "https://your-webhook-endpoint.com/guardrail"
  timeout: 10
  
  # Security
  hmac_secret: "your-webhook-secret"
  verify_ssl: true
  
  # Retry configuration
  max_retries: 3
  retry_delay: 1.0
  
  # What to send
  send_on_block: true
  send_on_pii: true
  send_on_error: false
```

## 🌐 Environment Variables

You can override any configuration using environment variables:

```bash
# LLM Configuration
export WAGTAIL_LLM_PROVIDER="openai"
export WAGTAIL_LLM_MODEL="gpt-4"
export WAGTAIL_LLM_API_KEY="sk-your-key"

# Security
export WAGTAIL_SECURITY_ENABLE_PII="true"
export WAGTAIL_SECURITY_MAX_PROMPT_LENGTH="10000"

# API
export WAGTAIL_API_DEFAULT_KEY="your-api-key"

# Logging
export WAGTAIL_LOGGING_LEVEL="INFO"
export WAGTAIL_LOGGING_FILE="logs/gateway.log"
```

## 🔄 Configuration Validation

### Validate Configuration

```bash
# Test configuration loading
python -c "from config_loader import load_config; print('✅ Configuration valid')"

# Test specific provider
curl http://localhost:8000/health
```

### Common Configuration Errors

**Error: "Provider not configured"**
```yaml
# Fix: Ensure provider is set
llm:
  provider: "ollama"  # Must be specified
```

**Error: "API key missing"**
```bash
# Fix: Set environment variable
export OPENAI_API_KEY="your-key-here"
```

**Error: "Invalid YAML syntax"**
```bash
# Fix: Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/sys_config.yaml'))"
```

## 🚀 Performance Tuning

### High-Throughput Configuration

```yaml
llm:
  timeout: 10  # Shorter timeout
  max_retries: 1  # Fewer retries

security:
  enable_pii_detection: false  # Disable for speed
  
api:
  rate_limit_per_minute: 1000  # Higher limits

logging:
  level: "WARNING"  # Less verbose logging
```

### Memory Optimization

```yaml
logging:
  max_size_mb: 10  # Smaller log files
  backup_count: 2  # Fewer backups

security:
  max_prompt_length: 2000  # Smaller prompts
```

## 📞 Getting Help

- **📚 Next Steps**: [API Reference](API-Reference)
- **🛡️ Security**: [Security Features](Security-Features)
- **💬 Community**: [GitHub Discussions](../../discussions)
- **🐛 Issues**: [Report Configuration Issues](../../issues)

---

**⚙️ Configuration complete! Your Wag-Tail AI Gateway v4.1.0 OSS Edition is now customized for your environment.**