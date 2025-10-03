# 🚀 Smart Agriculture Dashboard - Deployment Guide

This guide covers deploying the Smart Agriculture Dashboard to various platforms and environments.

## 📋 Prerequisites

### **System Requirements**
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+ (optional, SQLite works for development)
- 2GB+ RAM
- 10GB+ storage

### **Environment Variables**
```env
# AI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://ai.liara.ir/api/v1/your-endpoint
OPENAI_MODEL_NAME=openai/gpt-4o-mini

# Database
DATABASE_URL=sqlite:///./smart_dashboard.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/smart_dashboard

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Security
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 🐳 Docker Deployment

### **1. Create Dockerfile**
```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install Node.js and frontend dependencies
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && cd frontend \
    && npm install \
    && npm run build

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "start_server.py"]
```

### **2. Create docker-compose.yml**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_API_BASE=${OPENAI_API_BASE}
      - DATABASE_URL=sqlite:///./smart_dashboard.db
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

### **3. Deploy with Docker**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## ☁️ Cloud Deployment

### **AWS Deployment**

#### **1. EC2 Instance**
```bash
# Launch EC2 instance (Ubuntu 20.04)
# Install dependencies
sudo apt update
sudo apt install python3.9 python3-pip nodejs npm nginx

# Clone repository
git clone https://github.com/your-username/smart-agriculture-dashboard.git
cd smart-agriculture-dashboard

# Install dependencies
pip3 install -r requirements.txt
cd frontend && npm install && npm run build

# Configure nginx
sudo nano /etc/nginx/sites-available/smart-dashboard
```

#### **2. Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### **3. Systemd Service**
```ini
# /etc/systemd/system/smart-dashboard.service
[Unit]
Description=Smart Agriculture Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/smart-agriculture-dashboard
Environment=PATH=/home/ubuntu/smart-agriculture-dashboard/venv/bin
ExecStart=/home/ubuntu/smart-agriculture-dashboard/venv/bin/python start_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### **DigitalOcean Deployment**

#### **1. Droplet Setup**
```bash
# Create droplet (Ubuntu 20.04)
# Install dependencies
sudo apt update
sudo apt install python3.9 python3-pip nodejs npm nginx certbot python3-certbot-nginx

# Clone and setup
git clone https://github.com/your-username/smart-agriculture-dashboard.git
cd smart-agriculture-dashboard
pip3 install -r requirements.txt
cd frontend && npm install && npm run build
```

#### **2. SSL Certificate**
```bash
# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Heroku Deployment**

#### **1. Create Heroku App**
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=your-api-key
heroku config:set OPENAI_API_BASE=your-api-base
```

#### **2. Create Procfile**
```
web: python start_server.py
```

#### **3. Deploy**
```bash
# Add Heroku remote
git remote add heroku https://git.heroku.com/your-app-name.git

# Deploy
git push heroku main
```

## 🔧 Production Configuration

### **1. Environment Setup**
```bash
# Create production environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### **2. Database Setup**
```bash
# For PostgreSQL
sudo -u postgres createdb smart_dashboard
sudo -u postgres createuser dashboard_user
sudo -u postgres psql -c "ALTER USER dashboard_user PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smart_dashboard TO dashboard_user;"
```

### **3. Frontend Build**
```bash
cd frontend
npm install
npm run build
```

### **4. Production Server**
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## 🔒 Security Configuration

### **1. Firewall Setup**
```bash
# UFW (Ubuntu)
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### **2. SSL/TLS Configuration**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
}
```

### **3. Environment Security**
```bash
# Set secure permissions
chmod 600 .env
chmod 700 /path/to/your/app

# Use environment variables
export OPENAI_API_KEY="your-secure-key"
export DATABASE_URL="your-secure-database-url"
```

## 📊 Monitoring & Logging

### **1. Application Logs**
```python
# Configure logging in start_server.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### **2. System Monitoring**
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor resources
htop
iotop
nethogs
```

### **3. Log Rotation**
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/smart-dashboard

# Add:
/path/to/your/app/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
```

## 🚀 CI/CD Pipeline

### **1. GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        cd frontend && npm install
    
    - name: Run tests
      run: |
        python -m pytest tests/
        cd frontend && npm test
    
    - name: Deploy to server
      run: |
        # Add your deployment commands here
        echo "Deploying to production..."
```

### **2. Automated Deployment**
```bash
# Create deployment script
#!/bin/bash
# deploy.sh

echo "Starting deployment..."

# Pull latest changes
git pull origin main

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && npm run build

# Restart services
sudo systemctl restart smart-dashboard
sudo systemctl reload nginx

echo "Deployment completed!"
```

## 🔄 Backup & Recovery

### **1. Database Backup**
```bash
# SQLite backup
cp smart_dashboard.db backup_$(date +%Y%m%d_%H%M%S).db

# PostgreSQL backup
pg_dump smart_dashboard > backup_$(date +%Y%m%d_%H%M%S).sql
```

### **2. Application Backup**
```bash
# Create backup script
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/smart-dashboard"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /path/to/your/app
```

### **3. Automated Backups**
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

## 🎯 Performance Optimization

### **1. Database Optimization**
```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### **2. Caching**
```python
# Add Redis caching
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Cache frequently accessed data
def get_cached_data(key):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None
```

### **3. CDN Configuration**
```nginx
# Serve static files through CDN
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 📞 Troubleshooting

### **Common Issues**

1. **Port Already in Use**
   ```bash
   sudo lsof -i :8000
   sudo kill -9 PID
   ```

2. **Permission Denied**
   ```bash
   sudo chown -R $USER:$USER /path/to/your/app
   chmod +x start_server.py
   ```

3. **Database Connection Issues**
   ```bash
   # Check database status
   sudo systemctl status postgresql
   # or for SQLite
   ls -la smart_dashboard.db
   ```

4. **Frontend Build Issues**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### **Log Analysis**
```bash
# View application logs
tail -f app.log

# View system logs
sudo journalctl -u smart-dashboard -f

# View nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

**🚀 Your Smart Agriculture Dashboard is now ready for production deployment!**
