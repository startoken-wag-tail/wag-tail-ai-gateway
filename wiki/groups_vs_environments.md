# Groups vs Environments - Architecture Guide

## Overview

Wag-Tail AI Gateway uses two distinct concepts that should not be confused:
1. **Groups** - Logical divisions within an organization
2. **Environments** - Separate deployments of the AI Gateway

## Groups

Groups represent teams, departments, or projects within your organization that need separate rate limits or LLM configurations.

### Purpose
- **Internal cost allocation** - Track which team uses how much
- **Resource management** - Prevent one team from consuming all quota
- **Custom LLM routing** - Different teams may need different models

### Examples
```yaml
groups:
  "Acme Corporation":
    "engineering":      # Engineering team
      limit: 400000     # 40% of monthly quota
      llm_model: "gpt-4o"
    "marketing":        # Marketing team 
      limit: 300000     # 30% of monthly quota
      llm_model: "gpt-3.5-turbo"
    "support":          # Customer support team
      limit: 200000     # 20% of monthly quota
      llm_model: "gpt-3.5-turbo"
```

### How to Use
Pass the group ID in the request header:
```bash
curl -X POST http://gateway.example.com/chat \
  -H "x-api-key: your-api-key" \
  -H "x-group-id: engineering" \
  -d '{"prompt": "Hello"}'
```

## Environments

Environments are completely separate deployments of the AI Gateway, typically running on different infrastructure.

### Purpose
- **Isolation** - Changes in dev don't affect production
- **Testing** - Validate changes before production deployment
- **Risk management** - Production stability

### Examples
```
Production:    https://api.company.com        (AWS, high availability)
Staging:       https://staging-api.company.com (AWS, single instance)
Development:   https://dev-api.company.com     (Local server)
```

### Key Points
- Each environment has its **own configuration files**
- Each environment has its **own rate limit counters**
- Each environment uses the **same license.json**
- Each environment has the **same group configuration**

## Common Misconceptions

### ❌ WRONG: Creating "development" or "staging" as group names
```yaml
# DON'T DO THIS
groups:
  "MyCompany":
    "development": 25000   # ❌ Wrong - this is not a team
    "staging": 15000       # ❌ Wrong - this is not a team
    "production": 60000    # ❌ Wrong - this is not a team
```

### ✅ CORRECT: Using actual team/department names
```yaml
# DO THIS INSTEAD
groups:
  "MyCompany":
    "engineering": 400000  # ✅ Actual team
    "marketing": 300000    # ✅ Actual team
    "support": 200000      # ✅ Actual team
```

## Rate Limiting Architecture

### Per Environment
Each environment deployment gets the full monthly limit from the license:
- Production: 1,000,000 requests/month
- Staging: 1,000,000 requests/month (separate counter)
- Development: 1,000,000 requests/month (separate counter)

### Per Group (within each environment)
Groups share their environment's monthly limit:
```
Production Environment (1M total):
  - Engineering: 400k allocated
  - Marketing: 300k allocated
  - Support: 200k allocated
  - Unallocated: 100k (shared pool)

Staging Environment (1M total):
  - Engineering: 400k allocated (separate counter from prod)
  - Marketing: 300k allocated (separate counter from prod)
  - Support: 200k allocated (separate counter from prod)
  - Unallocated: 100k (shared pool)
```

## Environment-Specific Configuration

If you need different LLM models or costs per environment, consider:

### Option 1: Environment Variables
```bash
# Development
export LLM_OVERRIDE_PROVIDER=mistral
export LLM_OVERRIDE_MODEL=mistral-small

# Production
export LLM_OVERRIDE_PROVIDER=openai
export LLM_OVERRIDE_MODEL=gpt-4o
```

### Option 2: Separate Config Files
```
/config/
  group_config.yaml           # Same for all environments
  llm_routing.yaml           # Same for all environments
  llm_routing.dev.yaml       # Development overrides
  llm_routing.prod.yaml      # Production overrides
```

### Option 3: Cost Controls (Future Feature)
```yaml
# Future feature - not yet implemented
environment_limits:
  development:
    max_llm_spend_monthly: 100    # USD
    default_provider: "mistral"
  production:
    max_llm_spend_monthly: 5000   # USD
    default_provider: "openai"
```

## Best Practices

1. **Name groups after real teams** - engineering, marketing, support
2. **Keep group config consistent** - Same groups in all environments
3. **Use environment detection** - Let the gateway know which environment it's in
4. **Monitor separately** - Track usage per environment
5. **Test in staging** - Validate group limits work before production

## Admin Portal Implications

The Admin Portal's Group Management section:
- Shows groups for your organization
- Displays allocation vs license limit
- Validates total allocation ≤ monthly limit
- Same configuration applies to ALL environments

## Summary

- **Groups** = Teams within your company (engineering, marketing)
- **Environments** = Separate deployments (production, staging, dev)
- **Don't mix them** - Never create groups named "production" or "staging"
- **Each environment** = Full license limit with same group structure