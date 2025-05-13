# Lost and Found Application - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [SSL Configuration](#ssl-configuration)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites
- Python 3.11 or higher
- PostgreSQL 12 or higher
- Nginx
- Supervisor
- Virtual environment
- Git

## Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/lost-found-app.git
cd lost-found-app
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the project root:
```bash
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/lostfound
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
UPLOAD_FOLDER=static/uploads
```

## Database Setup

### 1. Create Database
```bash
createdb lostfound
```

### 2. Initialize Database
```bash
flask db upgrade
```

### 3. Create Admin User
```bash
python fix_admin.py
```

## Application Deployment

### 1. Configure Gunicorn
Create `gunicorn_config.py`:
```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gevent"
timeout = 120
```

### 2. Configure Supervisor
Create `/etc/supervisor/conf.d/lostfound.conf`:
```ini
[program:lostfound]
command=/path/to/venv/bin/gunicorn -c gunicorn_config.py app:app
directory=/path/to/lost-found-app
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/lostfound.err.log
stdout_logfile=/var/log/lostfound.out.log
```

### 3. Configure Nginx
Create `/etc/nginx/sites-available/lostfound`:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/lost-found-app/static;
    }
}
```

### 4. Enable the Site
```bash
sudo ln -s /etc/nginx/sites-available/lostfound /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL Configuration

### 1. Install Certbot
```bash
sudo apt-get install certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate
```bash
sudo certbot --nginx -d your_domain.com
```

## Monitoring and Maintenance

### 1. Log Rotation
Configure log rotation in `/etc/logrotate.d/lostfound`:
```bash
/var/log/lostfound.*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        supervisorctl restart lostfound
    endscript
}
```

### 2. Backup Database
Create a backup script `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump lostfound > $BACKUP_DIR/lostfound_$DATE.sql
find $BACKUP_DIR -type f -mtime +7 -delete
```

### 3. Regular Maintenance Tasks
- Monitor disk space
- Check application logs
- Update dependencies
- Backup database
- Review security patches

## Troubleshooting

### Common Issues
1. **Application Not Starting**
   - Check supervisor logs
   - Verify environment variables
   - Check database connection

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials
   - Ensure database exists

3. **File Upload Issues**
   - Check directory permissions
   - Verify disk space
   - Check file size limits

### Support
For additional support, contact:
- Email: support@lostandfound.com
- Documentation: https://docs.lostandfound.com 