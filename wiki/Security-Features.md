# 🛡️ Security Features - v4.1.0 OSS Edition

Comprehensive guide to Wag-Tail AI Gateway v4.1.0 OSS Edition's enterprise-grade security features.

## 🔒 Security Pipeline Overview

Wag-Tail implements a **multi-layer security pipeline** that processes every request through multiple security checks:

```
📥 Request → 🔐 Auth → 🛡️ Basic Guard → 🔍 PII Guard → 🤖 LLM → 🚫 Output Filter → 📤 Response
```

### Security Layers

1. **🔐 Authentication**: API key validation
2. **🛡️ Basic Security**: Regex filtering & code detection
3. **🔍 PII Protection**: Personal data detection & masking
4. **🔗 Webhook Integration**: External security validation
5. **🚫 Output Filtering**: Response sanitization

## 🔐 Authentication & Authorization

### API Key Authentication

**Default Configuration:**
```yaml
# config/sys_config.yaml
api:
  default_api_key: "demo-key-for-testing"
  require_api_key: true
```

**Request Example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world"}'
```

**Authentication Flow:**
1. Extract API key from `X-API-Key` header
2. Validate against configured keys
3. Log authentication attempts
4. Block invalid requests with 401 status

### Security Best Practices

- ✅ **Use strong API keys** (32+ characters, random)
- ✅ **Rotate keys regularly** (every 90 days)
- ✅ **Use HTTPS in production** (TLS 1.2+)
- ✅ **Monitor authentication logs**
- ❌ **Never log API keys in plaintext**

## 🛡️ Basic Security Guard

### SQL Injection Detection

**Blocked Patterns:**
```regex
# Common SQL injection patterns
(?i)(drop|delete|insert|update|create|alter)\s+(table|database|index)
(?i)union\s+select
(?i)or\s+1\s*=\s*1
(?i)'.*'.*or.*'.*'
(?i)exec\s*\(
```

**Example - Blocked Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "DROP TABLE users; --"}'
```

**Response:**
```json
{
  "response": "",
  "flag": "blocked",
  "reason": "SQL injection pattern detected",
  "llm_provider": "security_filter",
  "llm_model_name": "basic_guard"
}
```

### Code Execution Detection

**Blocked Code Patterns:**
```regex
# Python code execution
(?i)import\s+os
(?i)exec\s*\(
(?i)eval\s*\(
(?i)__import__\s*\(

# Shell commands
(?i)rm\s+-rf
(?i)sudo\s+
(?i)chmod\s+777

# JavaScript injection
(?i)<script.*>
(?i)document\.cookie
(?i)window\.location
```

**Example - Blocked Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "import os; os.system(\"rm -rf /\")"}'
```

### Custom Security Rules

**Add Custom Patterns:**
```yaml
# config/sys_config.yaml
security:
  enable_regex_filtering: true
  blocked_patterns:
    - "password\\s*[:=]\\s*[\"']?\\w+[\"']?"
    - "api[_-]?key\\s*[:=]\\s*[\"']?[a-zA-Z0-9]+[\"']?"
    - "secret\\s*[:=]\\s*[\"']?\\w+[\"']?"
    - "(?i)confidential"
    - "(?i)internal\\s+use\\s+only"
```

## 🔍 PII Detection & Protection

### Supported PII Types

| PII Type | Description | Example | Detection Method |
|----------|-------------|---------|------------------|
| **EMAIL_ADDRESS** | Email addresses | `john@example.com` | Regex + NLP |
| **PHONE_NUMBER** | Phone numbers | `+1-555-123-4567` | Regex patterns |
| **CREDIT_CARD** | Credit card numbers | `4111-1111-1111-1111` | Luhn algorithm |
| **SSN** | Social Security Numbers | `123-45-6789` | Format validation |
| **PERSON** | Person names | `John Smith` | NLP recognition |
| **LOCATION** | Addresses/locations | `123 Main St, NYC` | NLP recognition |
| **DATE_TIME** | Dates and times | `2025-01-15 14:30` | Pattern matching |
| **IP_ADDRESS** | IP addresses | `192.168.1.1` | Regex validation |
| **URL** | Web URLs | `https://example.com` | URL parsing |
| **CRYPTO** | Crypto addresses | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` | Format validation |

### PII Detection Configuration

```yaml
# config/sys_config.yaml
security:
  enable_pii_detection: true
  pii_confidence_threshold: 0.8  # 0.0 to 1.0
  pii_action: "block"  # "block", "mask", or "log"
  
  # Specific PII types to detect
  pii_types:
    - "CREDIT_CARD"
    - "EMAIL_ADDRESS"
    - "PHONE_NUMBER"
    - "SSN"
    - "PERSON"
```

### PII Detection Examples

**Email Detection:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My email is john.doe@company.com"}'
```

**Response:**
```json
{
  "response": "",
  "flag": "blocked",
  "reason": "High-confidence PII detected: EMAIL_ADDRESS",
  "llm_provider": "pii_guard",
  "llm_model_name": "presidio",
  "pii_detected": true,
  "pii_types": ["EMAIL_ADDRESS"]
}
```

**Credit Card Detection:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "My card number is 4111 1111 1111 1111"}'
```

### PII Masking (Alternative to Blocking)

```yaml
# config/sys_config.yaml
security:
  pii_action: "mask"  # Mask instead of block
```

**Masked Response Example:**
```json
{
  "response": "Your email ****@***.com has been processed",
  "flag": "safe",
  "pii_detected": true,
  "pii_types": ["EMAIL_ADDRESS"],
  "pii_masked": true
}
```

## 🔗 Webhook Security Integration

### External GuardRail Integration

```yaml
# config/sys_config.yaml
webhook:
  enabled: true
  url: "https://your-security-service.com/validate"
  timeout: 10
  
  # HMAC signing for security
  hmac_secret: "your-webhook-secret-key"
  verify_ssl: true
  
  # Retry configuration
  max_retries: 3
  retry_delay: 1.0
```

### Webhook Request Format

**Sent to Your Webhook:**
```json
{
  "prompt": "User input text",
  "timestamp": "2025-08-16T10:30:00Z",
  "client_ip": "192.168.1.100",
  "api_key_hash": "sha256_hash_of_api_key",
  "request_id": "req_abc123",
  "security_flags": {
    "pii_detected": false,
    "code_detected": false,
    "sql_detected": false
  }
}
```

**Expected Webhook Response:**
```json
{
  "allowed": true,
  "reason": "Request approved",
  "confidence": 0.95,
  "additional_checks": ["external_blacklist", "content_policy"]
}
```

### HMAC Signature Verification

**Python Webhook Example:**
```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    """Verify HMAC signature"""
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)

# In your webhook handler
def handle_webhook(request):
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.body
    
    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        return {"error": "Invalid signature"}, 401
    
    data = json.loads(payload)
    # Your security logic here
    
    return {"allowed": True, "reason": "Approved"}
```

## 🚫 Output Filtering

### Response Security

**Output filters process LLM responses to:**
- Remove sensitive information that might be leaked
- Block inappropriate content
- Sanitize code snippets
- Mask any remaining PII in responses

**Configuration:**
```yaml
# config/sys_config.yaml
security:
  enable_output_filtering: true
  output_filters:
    - "remove_api_keys"
    - "mask_emails"
    - "sanitize_code"
```

## 📊 Security Monitoring & Logging

### Security Event Logging

**Logged Security Events:**
- Authentication failures
- Blocked requests (SQL injection, code execution, PII)
- Webhook validation results
- Rate limit violations
- Unusual request patterns

**Example Security Log:**
```json
{
  "timestamp": "2025-08-16T10:30:00Z",
  "level": "WARNING",
  "message": "Request blocked by security filter",
  "event_type": "security_block",
  "reason": "SQL injection pattern detected",
  "client_ip": "192.168.1.100",
  "api_key_hash": "sha256_hash",
  "prompt_preview": "DROP TABLE...",
  "pattern_matched": "(?i)drop\\s+table",
  "request_id": "req_abc123"
}
```

### Security Metrics

**Monitor these security metrics:**
- Blocked requests per hour/day
- PII detection rate
- Authentication failure rate
- Most common attack patterns
- Response time impact of security checks

**Log Analysis Commands:**
```bash
# Monitor security blocks
grep "security_block" logs/wag_tail_gateway.log | tail -10

# Count PII detections
grep "pii_detected" logs/wag_tail_gateway.log | wc -l

# Check authentication failures
grep "Authentication failed" logs/wag_tail_gateway.log
```

## 🔧 Security Configuration Examples

### High Security (Production)

```yaml
# config/environments/production.yaml
security:
  enable_pii_detection: true
  enable_code_detection: true
  enable_regex_filtering: true
  
  pii_confidence_threshold: 0.9
  pii_action: "block"
  
  max_prompt_length: 2000
  
  blocked_patterns:
    - "(?i)(drop|delete|insert|update|create|alter)\\s+(table|database)"
    - "(?i)rm\\s+-rf"
    - "(?i)sudo"
    - "password\\s*[:=]"
    - "api[_-]?key\\s*[:=]"

webhook:
  enabled: true
  url: "https://security.company.com/validate"
  hmac_secret: "${WEBHOOK_SECRET}"
  timeout: 5

api:
  require_api_key: true
  rate_limit_per_minute: 30

logging:
  level: "WARNING"
  mask_sensitive_data: true
```

### Development (Relaxed)

```yaml
# config/environments/development.yaml
security:
  enable_pii_detection: true
  enable_code_detection: false  # Allow code for testing
  enable_regex_filtering: true
  
  pii_confidence_threshold: 0.7
  pii_action: "log"  # Log but don't block
  
  max_prompt_length: 50000  # Longer prompts for testing

webhook:
  enabled: false  # Disable for local development

api:
  rate_limit_per_minute: 1000  # Higher limit for testing

logging:
  level: "DEBUG"
  mask_sensitive_data: false  # Full logging for debugging
```

## 🧪 Security Testing

### Test Security Features

**Test SQL Injection Detection:**
```bash
python -c "
import requests
response = requests.post(
    'http://localhost:8000/chat',
    headers={'X-API-Key': 'demo-key-for-testing'},
    json={'prompt': 'DROP TABLE users; --'}
)
print('SQL injection blocked:', response.json()['flag'] == 'blocked')
"
```

**Test PII Detection:**
```bash
python -c "
import requests
response = requests.post(
    'http://localhost:8000/chat',
    headers={'X-API-Key': 'demo-key-for-testing'},
    json={'prompt': 'My SSN is 123-45-6789'}
)
print('PII detected:', response.json().get('pii_detected', False))
"
```

**Run Full Security Test Suite:**
```bash
python total_test_OSS.py
```

## 🚨 Security Incident Response

### When Security is Triggered

1. **Immediate Action**: Request is blocked/masked
2. **Logging**: Security event is logged with details
3. **Monitoring**: Metrics are updated
4. **Alerting**: Webhook notifications (if configured)

### Investigation Steps

1. **Check logs** for security events
2. **Analyze patterns** in blocked requests
3. **Review client behavior** for abuse
4. **Update security rules** if needed
5. **Consider IP blocking** for repeated violations

### Security Updates

- **Regular Updates**: Keep security patterns updated
- **Threat Intelligence**: Monitor new attack vectors
- **Community Input**: Contribute to security improvements
- **Custom Rules**: Add organization-specific patterns

## 📞 Getting Help

- **📚 Next Steps**: [Plugin Development](Plugin-Development)
- **🚀 Deployment**: [Deployment Guide](Deployment)
- **💬 Security Questions**: [GitHub Discussions](../../discussions)
- **🐛 Security Issues**: [Report Security Issues](../../issues)
- **🔒 Security Contact**: For responsible disclosure

---

**🛡️ Security Features complete! Your AI applications are now protected by Wag-Tail AI Gateway v4.1.0 OSS Edition's enterprise-grade security.**