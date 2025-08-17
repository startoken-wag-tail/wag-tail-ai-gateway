# ❓ FAQ & Troubleshooting - v4.1.0 OSS Edition

Comprehensive FAQ and troubleshooting guide for Wag-Tail AI Gateway v4.1.0 OSS Edition.

## 🔍 Quick Troubleshooting

### 1. Check System Health

```bash
# Health check
curl http://localhost:8000/health

# Expected healthy response
{
  "status": "healthy",
  "version": "4.1.0",
  "edition": "oss",
  "llm_status": "available",
  "plugins_loaded": 3
}
```

### 2. Run Test Suite

```bash
# Full system test
python total_test_OSS.py

# Expected: 50/50 tests passing (100% success rate)
```

### 3. Check Logs

```bash
# View recent logs
tail -f logs/wag_tail_gateway.log

# Search for errors
grep -i error logs/wag_tail_gateway.log

# Check specific issues
grep -i "blocked\|pii\|security" logs/wag_tail_gateway.log
```

## 🚀 Installation & Setup

### Q: Python version compatibility issues

**Error:** `ModuleNotFoundError` or version conflicts

**Solution:**
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Use specific Python version
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# For macOS with multiple Python versions
which python3
/usr/bin/python3 -m venv venv
```

### Q: Dependencies installation fails

**Error:** `pip install` fails with compilation errors

**Solution:**
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install build tools (Ubuntu/Debian)
sudo apt update
sudo apt install build-essential python3-dev

# Install build tools (CentOS/RHEL)
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# For macOS
xcode-select --install
```

### Q: Virtual environment issues

**Error:** `venv` not found or activation fails

**Solution:**
```bash
# Install venv if missing (Ubuntu/Debian)
sudo apt install python3-venv

# Create and activate properly
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows CMD
# or
venv\Scripts\Activate.ps1  # Windows PowerShell
```

## ⚙️ Configuration Issues

### Q: LLM provider not working

**Error:** `"llm_status": "unavailable"` in health check

**Ollama Issues:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama service
ollama serve

# Pull model if missing
ollama pull mistral

# Check model list
ollama list
```

**OpenAI Issues:**
```bash
# Verify API key
export OPENAI_API_KEY="sk-your-key-here"
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Test API key in Python
python3 -c "
import openai
openai.api_key = 'sk-your-key'
print(openai.Model.list())
"
```

**Configuration Check:**
```bash
# Validate YAML syntax
python3 -c "
import yaml
with open('config/sys_config.yaml') as f:
    config = yaml.safe_load(f)
    print('✅ Configuration valid')
    print(f'LLM Provider: {config.get(\"llm\", {}).get(\"provider\")}')
"
```

### Q: Environment variables not loading

**Error:** Configuration defaults being used instead of environment variables

**Solution:**
```bash
# Check environment variables
env | grep WAGTAIL
env | grep OPENAI

# Set in current session
export WAGTAIL_ENVIRONMENT=production
export OPENAI_API_KEY=your-key

# Make permanent (Ubuntu/Debian)
echo 'export OPENAI_API_KEY=your-key' >> ~/.bashrc
source ~/.bashrc

# Check variable in Python
python3 -c "import os; print(os.environ.get('OPENAI_API_KEY', 'NOT SET'))"
```

### Q: Configuration file not found

**Error:** `FileNotFoundError: config/sys_config.yaml`

**Solution:**
```bash
# Check current directory
pwd
ls -la config/

# Copy example configuration
cp config/sys_config.yaml.example config/sys_config.yaml

# Verify file permissions
ls -la config/sys_config.yaml
chmod 644 config/sys_config.yaml
```

## 🔐 Authentication & API Issues

### Q: API key authentication fails

**Error:** `401 Unauthorized` or `"Invalid API key"`

**Solution:**
```bash
# Check API key in configuration
grep -A 5 "api:" config/sys_config.yaml

# Test with correct header format
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# Common header mistakes (WRONG)
curl -H "API-Key: demo-key"           # Missing X- prefix
curl -H "Authorization: Bearer demo"  # Wrong header type
curl -H "X-Api-Key: demo-key"        # Wrong capitalization
```

### Q: CORS errors in browser

**Error:** `Access-Control-Allow-Origin` errors

**Solution:**
```yaml
# config/sys_config.yaml
api:
  cors_origins: 
    - "http://localhost:3000"  # Your frontend URL
    - "https://yourdomain.com"
    - "*"  # Allow all (development only)
```

### Q: Rate limiting triggered unexpectedly

**Error:** `429 Too Many Requests`

**Solution:**
```yaml
# Increase rate limit
api:
  rate_limit_per_minute: 120  # Increase from default 60

# Or disable for testing
api:
  rate_limit_per_minute: 9999
```

## 🛡️ Security & PII Issues

### Q: PII detection not working

**Error:** PII not being detected or Presidio warnings

**Install Presidio:**
```bash
# Install PII detection dependencies
pip install presidio-analyzer presidio-anonymizer

# Download language models
python3 -c "
import spacy
spacy.cli.download('en_core_web_sm')
"

# Test PII detection
python3 -c "
from presidio_analyzer import AnalyzerEngine
analyzer = AnalyzerEngine()
results = analyzer.analyze(text='My email is john@example.com', language='en')
print(f'PII detected: {len(results) > 0}')
"
```

**Configuration:**
```yaml
# config/sys_config.yaml
security:
  enable_pii_detection: true
  pii_confidence_threshold: 0.8
  pii_action: "block"  # or "mask" or "log"
```

### Q: Security filters too strict

**Error:** Legitimate requests being blocked

**Solution:**
```yaml
# Reduce security sensitivity
security:
  enable_code_detection: false  # Temporarily disable
  pii_confidence_threshold: 0.9  # Higher threshold (less sensitive)
  
  # Remove overly broad patterns
  blocked_patterns:
    # - "(?i)password"  # Comment out broad patterns
    - "DROP TABLE"      # Keep specific dangerous patterns
```

### Q: Custom security rules not working

**Error:** Custom regex patterns not blocking content

**Solution:**
```bash
# Test regex patterns
python3 -c "
import re
pattern = r'(?i)your-pattern-here'
text = 'Your test text'
match = re.search(pattern, text)
print(f'Pattern matches: {match is not None}')
"

# Debug regex in config
grep -A 10 "blocked_patterns" config/sys_config.yaml
```

## 🌐 Network & Connectivity

### Q: Connection refused errors

**Error:** `Connection refused` when calling API

**Solutions:**
```bash
# Check if service is running
ps aux | grep python | grep main
netstat -tlnp | grep 8000

# Check firewall
sudo ufw status
sudo iptables -L

# Start service
uvicorn main:app --host 0.0.0.0 --port 8000

# Check binding address
curl http://127.0.0.1:8000/health  # Local only
curl http://0.0.0.0:8000/health     # All interfaces
```

### Q: Slow response times

**Error:** API responses taking >10 seconds

**Solutions:**
```bash
# Check LLM provider latency
time curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: demo-key-for-testing" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Quick test"}'

# Monitor system resources
top
htop
free -h
df -h

# Optimize configuration
# config/sys_config.yaml
llm:
  timeout: 15  # Reduce timeout
  max_retries: 1  # Fewer retries

security:
  enable_pii_detection: false  # Disable for speed testing
```

### Q: Docker networking issues

**Error:** Container can't reach external services

**Solution:**
```bash
# Check Docker network
docker network ls
docker inspect bridge

# Test from inside container
docker exec -it container_name curl http://host.docker.internal:11434

# Use host networking (development)
docker run --network host your-image

# Environment specific URLs
# docker-compose.yml
environment:
  - OLLAMA_URL=http://host.docker.internal:11434
```

## 🚀 Performance Issues

### Q: High memory usage

**Error:** Application consuming too much RAM

**Solutions:**
```bash
# Monitor memory usage
ps aux | grep python
free -h

# Reduce worker processes
# gunicorn.conf.py
workers = 2  # Reduce from 4

# Limit request size
# config/sys_config.yaml
security:
  max_prompt_length: 2000  # Reduce from 10000

# Check for memory leaks
python3 -c "
import psutil
import time
process = psutil.Process()
for i in range(10):
    print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
    time.sleep(1)
"
```

### Q: CPU usage spikes

**Error:** High CPU utilization

**Solutions:**
```bash
# Monitor CPU usage
top -p $(pgrep -f "main:app")

# Reduce concurrent processing
# Limit worker processes and connections
workers = 1
worker_connections = 100

# Profile application
pip install py-spy
py-spy top --pid $(pgrep -f "main:app")
```

### Q: Disk space issues

**Error:** Disk full or log files too large

**Solutions:**
```bash
# Check disk usage
df -h
du -sh logs/

# Rotate logs
# config/sys_config.yaml
logging:
  max_size_mb: 10    # Smaller log files
  backup_count: 2    # Fewer backups

# Clean old logs
find logs/ -name "*.log.*" -mtime +7 -delete

# Setup logrotate (Linux)
sudo nano /etc/logrotate.d/wagtail
```

## 🐳 Docker Issues

### Q: Docker build fails

**Error:** Build context or dependency issues

**Solutions:**
```bash
# Clean Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -t wagtail .

# Check build context size
du -sh .
# Add to .dockerignore:
venv/
logs/
__pycache__/
*.pyc
.git/
```

### Q: Container startup fails

**Error:** Container exits immediately

**Solutions:**
```bash
# Check container logs
docker logs container_name

# Run interactively for debugging
docker run -it --entrypoint /bin/bash wagtail

# Check environment variables
docker run wagtail env

# Test health check
docker run wagtail curl -f http://localhost:8000/health || echo "Health check failed"
```

### Q: Volume mounting issues

**Error:** Configuration or log files not persisting

**Solutions:**
```bash
# Check volume mounts
docker inspect container_name | grep -A 10 "Mounts"

# Correct volume syntax
docker run -v $(pwd)/config:/app/config wagtail
docker run -v /absolute/path/config:/app/config wagtail

# Fix permissions
sudo chown -R 1000:1000 config/
sudo chmod -R 644 config/
```

## 🔧 Development Issues

### Q: Hot reload not working

**Error:** Changes not reflected without restart

**Solutions:**
```bash
# Use reload flag
uvicorn main:app --reload

# Check file watching
pip install watchfiles

# Exclude problematic directories
uvicorn main:app --reload --reload-exclude "logs/*"
```

### Q: IDE/Editor integration

**Error:** Import errors or no code completion

**Solutions:**
```bash
# Activate virtual environment in IDE
which python  # Should show venv path

# Install development tools
pip install black flake8 mypy

# VS Code settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true
}
```

### Q: Testing issues

**Error:** Tests failing or not running

**Solutions:**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run specific test
python3 -m pytest test_oss.py -v

# Run with output
python3 -m pytest test_oss.py -s

# Check test environment
python3 -c "
import sys
print(f'Python: {sys.version}')
print(f'Path: {sys.path[:3]}')
"
```

## 📊 Monitoring & Logging

### Q: Logs not appearing

**Error:** No log output or logs in wrong location

**Solutions:**
```bash
# Check log configuration
grep -A 5 "logging:" config/sys_config.yaml

# Create log directory
mkdir -p logs
chmod 755 logs

# Test logging
python3 -c "
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')
logger.info('Test log message')
"

# Check log level
# config/sys_config.yaml
logging:
  level: "DEBUG"  # More verbose
  console: true   # Also log to console
```

### Q: Too much log noise

**Error:** Logs filled with unnecessary information

**Solutions:**
```yaml
# config/sys_config.yaml
logging:
  level: "WARNING"  # Less verbose
  
  # Mask sensitive data
  mask_sensitive_data: true
  mask_api_keys: true
  
  # Exclude noisy loggers
  loggers:
    uvicorn.access:
      level: "WARNING"
    httpx:
      level: "WARNING"
```

### Q: Performance monitoring

**Error:** No visibility into system performance

**Solutions:**
```bash
# Add monitoring endpoints
curl http://localhost:8000/health

# Monitor with external tools
# Install prometheus_client
pip install prometheus_client

# Basic monitoring script
python3 -c "
import time
import requests
import psutil

while True:
    try:
        resp = requests.get('http://localhost:8000/health', timeout=5)
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        print(f'Health: {resp.status_code}, CPU: {cpu}%, Memory: {memory}%')
    except Exception as e:
        print(f'Error: {e}')
    time.sleep(30)
"
```

## 🔄 Migration & Upgrades

### Q: Upgrading from older version

**Error:** Configuration or compatibility issues

**Solutions:**
```bash
# Backup current installation
cp -r wag-tail-ai-gateway wag-tail-ai-gateway.backup

# Check version differences
git log --oneline | head -10

# Update dependencies
pip install -r requirements.txt --upgrade

# Migrate configuration if needed
# Check for new config options in sys_config.yaml.example
```

### Q: Plugin compatibility

**Error:** Plugins not loading after update

**Solutions:**
```bash
# Check plugin versions
ls -la startoken-plugins/

# Update plugins
cd startoken-plugins/
git pull

# Check plugin logs
grep -i plugin logs/wag_tail_gateway.log

# Disable problematic plugins temporarily
# config/sys_config.yaml
plugins:
  problematic_plugin:
    enabled: false
```

## 📞 Getting Community Help

### Where to Get Help

1. **📚 Documentation**: Check all wiki pages first
2. **🔍 GitHub Issues**: Search existing issues
3. **💬 Discussions**: Join community discussions
4. **📧 Support**: Enterprise support available

### How to Report Issues

**Include this information:**

```bash
# System information
python3 --version
pip list | grep -E "(fastapi|uvicorn|pydantic)"
cat /etc/os-release  # Linux
sw_vers               # macOS

# Application information
curl http://localhost:8000/health
grep -A 5 "llm:" config/sys_config.yaml
ls -la logs/

# Error details
tail -50 logs/wag_tail_gateway.log
python3 total_test_OSS.py
```

### Common Error Patterns

**Search logs for these patterns:**

```bash
# Authentication issues
grep -i "invalid.*key\|unauthorized\|403" logs/

# LLM provider issues  
grep -i "llm.*error\|provider.*fail\|timeout" logs/

# Security blocks
grep -i "blocked\|security.*violation\|pii.*detected" logs/

# Configuration issues
grep -i "config.*error\|yaml.*error\|missing" logs/

# Network issues
grep -i "connection.*refused\|timeout\|network" logs/
```

## 🎯 Best Practices

### Prevention Tips

1. **Regular Health Checks**: Monitor `/health` endpoint
2. **Log Rotation**: Configure proper log management
3. **Resource Monitoring**: Watch CPU, memory, disk usage
4. **Regular Testing**: Run test suite periodically
5. **Configuration Validation**: Validate YAML syntax
6. **Security Updates**: Keep dependencies updated
7. **Backup Strategy**: Regular config and data backups

### Performance Optimization

1. **Resource Allocation**: Proper CPU/memory sizing
2. **LLM Provider Selection**: Choose based on needs
3. **Security Tuning**: Balance security vs. performance
4. **Caching Strategy**: Implement response caching
5. **Load Balancing**: Multiple instances for scale

---

**❓ FAQ complete! Most issues for Wag-Tail AI Gateway v4.1.0 OSS Edition should now be resolved. For additional help, visit [GitHub Discussions](../../discussions) or [report an issue](../../issues).**