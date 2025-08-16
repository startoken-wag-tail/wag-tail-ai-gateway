# Wag-Tail OSS Plugins Directory

This directory contains basic security plugins included with the OSS edition of Wag-Tail AI Gateway.

## Included Plugins

### Core Authentication & Security
- **wag_tail_key_auth**: API key authentication
- **wag_tail_basic_guard**: Regex-based security filters and code detection
- **wag_tail_pii_guard**: PII detection and masking using Microsoft Presidio
- **wag_tail_webhook_guardrail**: External GuardRail system integration

## Plugin Architecture

In the OSS edition, plugins are implemented directly in the `plugin_loader.py` file as lightweight Python classes. This approach provides:

- ✅ Zero external dependencies
- ✅ Fast loading and execution
- ✅ Easy customization and extension
- ✅ Built-in security features

## Advanced Plugins (Enterprise Only)

The following plugins are available only in the Enterprise edition:

- `wag_tail_priority_queue`: Weighted fair queuing system
- `wag_tail_semantic_cache`: Intelligent response caching
- `wag_tail_vault_integration`: HashiCorp Vault secret management
- `wag_tail_langfuse_telemetry`: Advanced observability and tracing
- `wag_tail_advanced_analytics`: Usage analytics and reporting
- `wag_tail_custom_models`: Custom fine-tuned model support

## Configuration

Plugins are configured in `config/sys_config.yaml`:

```yaml
plugins:
  enabled:
    - "wag_tail_key_auth"
    - "wag_tail_basic_guard"
    - "wag_tail_pii_guard"
    - "wag_tail_webhook_guardrail"
```

## Creating Custom Plugins

To create a custom plugin for the OSS edition:

1. Add your plugin class to `plugin_loader.py`
2. Implement the required methods (`get_status()`, etc.)
3. Add the plugin name to your configuration
4. Restart the gateway

Example plugin structure:
```python
class MyCustomPlugin:
    def __init__(self):
        self.name = "my_custom_plugin"
        self.version = "1.0.0"
    
    def process_request(self, request_data):
        # Your custom logic here
        return {"allowed": True}
    
    def get_status(self):
        return {
            "name": self.name,
            "version": self.version,
            "status": "active",
            "description": "My custom security plugin"
        }
```

## Security Best Practices

When developing custom plugins:

- ✅ Always validate input data
- ✅ Use proper error handling
- ✅ Log security events appropriately
- ✅ Follow the principle of least privilege
- ✅ Never log sensitive data (API keys, PII, etc.)

## Support

For plugin development support:
- Review the existing plugin implementations in `plugin_loader.py`
- Check the configuration examples in `config/sys_config.yaml`
- Refer to the main documentation in `README.md`