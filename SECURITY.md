# Security Policy

## Supported Versions

We actively support the following versions of Wag-Tail AI Gateway with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 4.0.x   | :white_check_mark: |
| 3.4.x   | :white_check_mark: |
| 3.3.x   | :white_check_mark: |
| < 3.3   | :x:                |

## Security Features

Wag-Tail AI Gateway includes multiple layers of security protection:

### 🔐 Input Security
- **API Key Authentication**: All requests require valid API keys
- **Request Validation**: JSON schema validation with Pydantic
- **Rate Limiting**: Per-organization and per-group limits
- **Input Sanitization**: Automatic cleaning of malicious input

### 🛡️ Content Filtering
- **Regex Pattern Matching**: SQL injection, command injection detection
- **Code Detection**: Multi-language code block detection and blocking
- **PII Detection**: Personal information detection and redaction using Microsoft Presidio
- **AI Classification**: ML-powered prompt analysis for security threats
- **Output Filtering**: Response content analysis and blocking

### 🔒 Data Protection
- **Secret Management**: HashiCorp Vault integration for secure credential storage
- **PII Masking**: Automatic masking of sensitive data in logs
- **Secure Headers**: Security headers in all responses
- **Environment Isolation**: Environment-aware configuration management

### 📊 Monitoring & Observability
- **Comprehensive Logging**: All security events logged with context
- **Real-time Monitoring**: Integration with external security systems
- **Webhook Integration**: Security event notifications to GuardRail systems
- **Audit Trails**: Complete request/response audit capabilities

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 🚨 For Critical Vulnerabilities

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities by emailing:
**security@wag-tail.com**

Include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes or mitigations

### 📧 Email Template

```
Subject: [SECURITY] Vulnerability Report - [Brief Description]

Vulnerability Details:
- Component affected: 
- Vulnerability type: 
- Severity assessment: 

Reproduction Steps:
1. 
2. 
3. 

Impact Assessment:
- 

Suggested Mitigation:
- 

Additional Information:
- 
```

### ⏱️ Response Timeline

- **Initial Response**: Within 24 hours of receiving the report
- **Initial Assessment**: Within 72 hours  
- **Fix Development**: Timeline depends on severity and complexity
- **Public Disclosure**: After fix is deployed and users have time to update

### 🏆 Security Researcher Recognition

We believe in recognizing security researchers who help improve our security:

- **Public Recognition**: Listed in our security acknowledgments (with permission)
- **Priority Support**: Fast-track support for future reports
- **Early Access**: Beta access to new security features (if desired)

## Security Best Practices

### For Developers

1. **Secure Configuration**
   ```yaml
   # Use environment-specific configurations
   security:
     pii_detection: true
     ai_classification: true
     output_filtering: true
   
   # Never commit secrets
   vault:
     enabled: true
     address: "${VAULT_ADDR}"
     token: "${VAULT_TOKEN}"
   ```

2. **API Key Management**
   ```bash
   # Use strong, unique API keys
   # Rotate keys regularly
   # Store keys securely (Vault, environment variables)
   ```

3. **Plugin Development**
   ```python
   # Validate all inputs
   # Sanitize outputs  
   # Follow principle of least privilege
   # Log security events
   ```

### For Deployments

1. **Network Security**
   - Use HTTPS/TLS for all communications
   - Configure firewalls and security groups
   - Implement network segmentation
   - Monitor network traffic

2. **Infrastructure Security**
   - Keep dependencies updated
   - Use container scanning
   - Implement proper access controls
   - Regular security audits

3. **Monitoring**
   ```yaml
   # Enable comprehensive logging
   log:
     log_level: "INFO"
     security_events: true
     audit_trail: true
   
   # Set up alerting
   monitoring:
     enabled: true
     security_alerts: true
   ```

## Security Configuration

### Recommended Security Settings

```yaml
# config/security.yaml
security:
  # Enable all security layers
  pii_detection:
    enabled: true
    confidence_threshold: 0.8
    
  ai_classification:
    enabled: true
    model: "distilbert-base-uncased"
    threshold: 0.7
    
  regex_filtering:
    enabled: true
    patterns:
      - sql_injection
      - command_injection
      - xss_attempts
      
  output_guard:
    enabled: true
    scan_responses: true
    block_sensitive: true

# Rate limiting
rate_limiting:
  enabled: true
  requests_per_minute: 60
  burst_limit: 100
  
# Authentication
authentication:
  api_key_required: true
  key_rotation_days: 90
  failed_attempt_lockout: 5
```

### Environment Variables

```bash
# Secure environment configuration
export VAULT_ADDR="https://vault.company.com"
export VAULT_TOKEN="your-vault-token"
export ADMIN_API_KEY="your-secure-admin-key"
export DATABASE_PASSWORD="your-secure-db-password"

# Security headers
export SECURITY_HEADERS_ENABLED=true
export CORS_ORIGINS="https://your-domain.com"
```

## Security Audit

### Regular Security Reviews

We recommend regular security reviews including:

1. **Code Review**: Security-focused code reviews for all changes
2. **Dependency Scanning**: Regular scanning for vulnerable dependencies
3. **Penetration Testing**: Periodic professional security assessments
4. **Configuration Review**: Regular review of security configurations

### Security Checklist

- [ ] All dependencies are up to date
- [ ] Security headers are configured
- [ ] API keys are rotated regularly
- [ ] Logs are monitored for security events
- [ ] Backup and recovery procedures are tested
- [ ] Access controls are properly configured
- [ ] Network security is implemented
- [ ] Incident response plan is in place

## Incident Response

### In Case of a Security Incident

1. **Immediate Response**
   - Isolate affected systems
   - Preserve evidence
   - Assess impact
   - Notify relevant stakeholders

2. **Investigation**
   - Analyze logs and evidence
   - Determine root cause
   - Assess extent of compromise
   - Document findings

3. **Remediation**
   - Apply security patches
   - Update configurations
   - Strengthen defenses
   - Monitor for continued threats

4. **Communication**
   - Notify users if necessary
   - Provide clear guidance
   - Document lessons learned
   - Update security procedures

## Security Resources

### Documentation
- [Admin API Security](docs/admin-api-introduction.md)
- [Plugin Security Guide](docs/startoken-plugin-framework.md)
- [Configuration Security](README.md#configuration)

### Tools and Dependencies
- [Microsoft Presidio](https://microsoft.github.io/presidio/) - PII detection
- [HashiCorp Vault](https://www.vaultproject.io/) - Secret management
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - Framework security
- [Pydantic](https://pydantic.dev/) - Data validation

### Security Community
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [AI Security Best Practices](https://owasp.org/www-project-ai-security-and-privacy-guide/)

## Contact

For security-related questions or concerns:
- **Security Team**: security@wag-tail.com
- **General Support**: opensource@wag-tail.com
- **General Questions**: Open a [GitHub Discussion](https://github.com/wagtail-ai/wag-tail-ai-gateway/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/wagtail-ai/wag-tail-ai-gateway/issues) (for non-security bugs only)

---

**Thank you for helping us keep Wag-Tail AI Gateway secure! 🔒**