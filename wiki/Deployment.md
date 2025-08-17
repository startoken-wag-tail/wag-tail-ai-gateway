# 🚀 Deployment Guide - v4.1.0 OSS Edition

Complete guide for deploying Wag-Tail AI Gateway v4.1.0 OSS Edition to production environments.

## 🏗️ Deployment Options

| Method | Complexity | Scalability | Use Case |
|--------|------------|-------------|----------|
| **Single Server** | Low | Small-Medium | Development, small teams |
| **Docker** | Medium | Medium-High | Containerized environments |
| **Cloud Platforms** | Medium | High | Production, enterprise |
| **Kubernetes** | High | Very High | Large scale, microservices |

## 🖥️ Single Server Deployment

### Prerequisites

```bash
# System requirements
- Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- Python 3.9+
- 4GB+ RAM
- 2+ CPU cores
- 20GB+ disk space
- Internet connectivity
```

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash wagtail
sudo usermod -aG sudo wagtail
```

### Step 2: Application Deployment

```bash
# Switch to application user
sudo su - wagtail

# Clone repository
git clone https://github.com/startoken-wag-tail/wag-tail-ai-gateway.git
cd wag-tail-ai-gateway

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production server
pip install gunicorn
```

### Step 3: Configuration

```bash
# Create production config
cp config/environments/production.yaml.example config/environments/production.yaml

# Edit production configuration
nano config/environments/production.yaml
```

**Production Configuration:**
```yaml
# config/environments/production.yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
  timeout: 15

security:
  enable_pii_detection: true
  enable_code_detection: true
  pii_confidence_threshold: 0.9
  max_prompt_length: 5000

api:
  default_api_key: "${WAGTAIL_API_KEY}"
  cors_origins: ["https://yourdomain.com"]
  rate_limit_per_minute: 60

logging:
  level: "WARNING"
  file: "/var/log/wagtail/gateway.log"
  max_size_mb: 100

webhook:
  enabled: true
  url: "${WEBHOOK_URL}"
  hmac_secret: "${WEBHOOK_SECRET}"
```

### Step 4: Environment Variables

```bash
# Create environment file
sudo nano /etc/environment

# Add environment variables
WAGTAIL_ENVIRONMENT=production
OPENAI_API_KEY=sk-your-openai-key-here
WAGTAIL_API_KEY=your-secure-api-key-here
WEBHOOK_URL=https://your-webhook.com/validate
WEBHOOK_SECRET=your-webhook-secret

# Create log directory
sudo mkdir -p /var/log/wagtail
sudo chown wagtail:wagtail /var/log/wagtail
```

### Step 5: Systemd Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/wagtail.service
```

**Service Configuration:**
```ini
[Unit]
Description=Wag-Tail AI Gateway v4.1.0 OSS Edition
After=network.target

[Service]
Type=notify
User=wagtail
Group=wagtail
WorkingDirectory=/home/wagtail/wag-tail-ai-gateway
Environment=PATH=/home/wagtail/wag-tail-ai-gateway/venv/bin
Environment=WAGTAIL_ENVIRONMENT=production
EnvironmentFile=/etc/environment
ExecStart=/home/wagtail/wag-tail-ai-gateway/venv/bin/gunicorn main:app \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable wagtail
sudo systemctl start wagtail
sudo systemctl status wagtail
```

### Step 6: Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/wagtail
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/wagtail /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: SSL/TLS Setup

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash wagtail && \
    chown -R wagtail:wagtail /app
USER wagtail

# Create log directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  wagtail:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WAGTAIL_ENVIRONMENT=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WAGTAIL_API_KEY=${WAGTAIL_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - wagtail
    restart: unless-stopped
```

### Docker Deployment Commands

```bash
# Create environment file
echo "OPENAI_API_KEY=your-key" > .env
echo "WAGTAIL_API_KEY=your-api-key" >> .env

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f wagtail

# Scale workers
docker-compose up -d --scale wagtail=3

# Update deployment
docker-compose pull
docker-compose up -d --force-recreate
```

## ☁️ Cloud Platform Deployment

### AWS Deployment

**Using AWS App Runner:**
```yaml
# apprunner.yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  runtime-version: 3.11
  command: uvicorn main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
  env:
    - name: WAGTAIL_ENVIRONMENT
      value: production
    - name: OPENAI_API_KEY
      value: your-key
```

**Using ECS:**
```json
{
  "family": "wagtail-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "wagtail",
      "image": "your-account.dkr.ecr.region.amazonaws.com/wagtail:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "WAGTAIL_ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/wagtail",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

**Using Cloud Run:**
```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: wagtail-gateway
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "1Gi"
        run.googleapis.com/cpu: "1000m"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/your-project/wagtail:latest
        ports:
        - containerPort: 8000
        env:
        - name: WAGTAIL_ENVIRONMENT
          value: production
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
```

### Azure Container Instances

```yaml
# aci-deployment.yaml
apiVersion: 2019-12-01
location: eastus
name: wagtail-gateway
properties:
  containers:
  - name: wagtail
    properties:
      image: your-registry.azurecr.io/wagtail:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 1
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: WAGTAIL_ENVIRONMENT
        value: production
      - name: OPENAI_API_KEY
        secureValue: your-openai-key
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8000
    dnsNameLabel: wagtail-gateway
  restartPolicy: Always
```

## ⚓ Kubernetes Deployment

### Kubernetes Manifests

**Deployment:**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wagtail-gateway
  labels:
    app: wagtail-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wagtail-gateway
  template:
    metadata:
      labels:
        app: wagtail-gateway
    spec:
      containers:
      - name: wagtail
        image: wagtail-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: WAGTAIL_ENVIRONMENT
          value: production
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: wagtail-secrets
              key: openai-api-key
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: wagtail-config
---
apiVersion: v1
kind: Service
metadata:
  name: wagtail-service
spec:
  selector:
    app: wagtail-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wagtail-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: wagtail-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: wagtail-service
            port:
              number: 80
```

**ConfigMap:**
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wagtail-config
data:
  production.yaml: |
    llm:
      provider: "openai"
      model: "gpt-3.5-turbo"
      timeout: 15
    security:
      enable_pii_detection: true
      enable_code_detection: true
      pii_confidence_threshold: 0.9
    api:
      cors_origins: ["https://yourdomain.com"]
      rate_limit_per_minute: 60
    logging:
      level: "WARNING"
```

**Secrets:**
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: wagtail-secrets
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  wagtail-api-key: <base64-encoded-key>
```

### Helm Chart

```yaml
# helm/wagtail/values.yaml
replicaCount: 3

image:
  repository: wagtail-gateway
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: wagtail-tls
      hosts:
        - api.yourdomain.com

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

config:
  environment: production
  llm:
    provider: openai
    model: gpt-3.5-turbo
    timeout: 15
  security:
    enable_pii_detection: true
    pii_confidence_threshold: 0.9
```

## 📊 Monitoring & Observability

### Application Monitoring

**Health Check Endpoint:**
```bash
# Kubernetes liveness probe
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "edition": "oss",
  "llm_status": "available",
  "plugins_loaded": 3
}
```

**Metrics Collection:**
```python
# custom_metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
REQUEST_COUNT = Counter('wagtail_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('wagtail_request_duration_seconds', 'Request duration')
ACTIVE_REQUESTS = Gauge('wagtail_active_requests', 'Active requests')

# Security metrics
BLOCKED_REQUESTS = Counter('wagtail_blocked_requests_total', 'Blocked requests', ['reason'])
PII_DETECTIONS = Counter('wagtail_pii_detections_total', 'PII detections', ['pii_type'])

# LLM metrics
LLM_REQUESTS = Counter('wagtail_llm_requests_total', 'LLM requests', ['provider', 'model'])
LLM_ERRORS = Counter('wagtail_llm_errors_total', 'LLM errors', ['provider', 'error_type'])
```

### Log Aggregation

**Structured Logging:**
```python
# Enhanced logging configuration
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## 🔒 Production Security

### Security Hardening

**System Security:**
```bash
# Firewall configuration
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # Don't expose app directly

# Fail2ban for SSH protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

**Application Security:**
```yaml
# Production security config
security:
  enable_pii_detection: true
  enable_code_detection: true
  enable_regex_filtering: true
  pii_confidence_threshold: 0.95  # Higher threshold
  max_prompt_length: 2000  # Stricter limit

api:
  require_api_key: true
  rate_limit_per_minute: 30  # Lower rate limit
  cors_origins: ["https://yourdomain.com"]  # Specific origins only

logging:
  level: "WARNING"  # Reduce log verbosity
  mask_sensitive_data: true
  file: "/var/log/wagtail/gateway.log"
```

### Secrets Management

**Using HashiCorp Vault:**
```python
# vault_integration.py
import hvac

client = hvac.Client(url='https://vault.yourdomain.com')
client.token = os.environ['VAULT_TOKEN']

# Read secrets
openai_key = client.secrets.kv.v2.read_secret_version(path='wagtail/openai')['data']['data']['api_key']
api_key = client.secrets.kv.v2.read_secret_version(path='wagtail/api')['data']['data']['key']
```

**Using Kubernetes Secrets:**
```bash
# Create secret from command line
kubectl create secret generic wagtail-secrets \
  --from-literal=openai-api-key=sk-your-key \
  --from-literal=wagtail-api-key=your-api-key
```

## 📈 Performance Optimization

### Application Tuning

**Gunicorn Configuration:**
```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4  # 2 * CPU cores
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 30
keepalive = 5
```

**Async Configuration:**
```python
# For high concurrency
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 2000
```

### Caching Strategy

**Redis Caching (Future Enhancement):**
```python
# Response caching
import redis
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_response(prompt, response, ttl=3600):
    """Cache LLM responses"""
    cache_key = f"wagtail:response:{hashlib.md5(prompt.encode()).hexdigest()}"
    redis_client.setex(cache_key, ttl, json.dumps(response))

def get_cached_response(prompt):
    """Get cached response"""
    cache_key = f"wagtail:response:{hashlib.md5(prompt.encode()).hexdigest()}"
    cached = redis_client.get(cache_key)
    return json.loads(cached) if cached else None
```

## 🚨 Disaster Recovery

### Backup Strategy

**Application Backup:**
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backup/wagtail/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration
cp -r /home/wagtail/wag-tail-ai-gateway/config $BACKUP_DIR/

# Backup logs
cp -r /var/log/wagtail $BACKUP_DIR/

# Create archive
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR.tar.gz s3://your-backup-bucket/wagtail/
```

**Database Backup (if using Advanced Edition):**
```bash
# SQLite backup
cp /home/wagtail/wag-tail-ai-gateway/data/wag_tail.db /backup/wagtail_db_$(date +%Y%m%d).db
```

### Recovery Procedures

**Service Recovery:**
```bash
# Check service status
sudo systemctl status wagtail

# Restart service
sudo systemctl restart wagtail

# View logs
sudo journalctl -u wagtail -f

# Rollback deployment
git checkout previous-version
sudo systemctl restart wagtail
```

## 📞 Getting Help

- **📚 Next Steps**: [FAQ & Troubleshooting](FAQ-&-Troubleshooting)
- **🧩 Customization**: [Plugin Development](Plugin-Development)
- **💬 Deployment Questions**: [GitHub Discussions](../../discussions)
- **🐛 Deployment Issues**: [Report Issues](../../issues)
- **📧 Enterprise Support**: For production deployment assistance

---

**🚀 Deployment complete! Your Wag-Tail AI Gateway v4.1.0 OSS Edition is now running in production with enterprise-grade security and reliability.**