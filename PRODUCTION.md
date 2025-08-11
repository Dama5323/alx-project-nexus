# Production Deployment Guide

## Prerequisites
- Python 3.11+
- PostgreSQL 14+ (or your DB)
- Redis (if using caching)
- Environment variables configured

## Environment Setup

### Required Variables
```bash
# Core Settings
SECRET_KEY=your-unique-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_prod_db
DB_USER=prod_user
DB_PASSWORD=secure_password
DB_HOST=prod-db.example.com
DB_PORT=5432

# Security
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

### Deployment Process
**Automated Deployment (Recommended)**
```bash
./deploy.sh production
```

### Manual Steps
1. **Install dependencies:**
```bash
pip install -r requirements/production.txt
```

2. **Run migrations:**
```bash
python manage.py migrate --settings=config.settings.production
```

3. **Collect static files:**
```bash
python manage.py collectstatic --noinput --settings=config.settings.production
```

### Health Checks
**Verify deployment health:**
```bash
curl https://yourdomain.com/health/
```

***Expected response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "cache": "ok"
  }
}
```
### Monitoring Essentials
1. **Required Checks:**
- Database connectivity
-Static files serving
-Background workers (if applicable)

2. **Log Locations:**
- Application logs: /var/log/your-app/app.log
- Error logs: /var/log/your-app/errors.log

### Critical Security Checklist
- DEBUG mode disabled
- HTTPS enforced
- Secure cookies enabled
- Admin path changed from /admin/

### Troubleshooting
 **Common Issues**
1. **Static Files 404:**
- Verify STATIC_ROOT setting
- Check WhiteNoise middleware order

2. **Database Connections:**
``` bash
python manage.py dbshell --settings=config.settings.production
```



### Key Differences from Development

| Aspect          | Production                     | Development               |
|-----------------|--------------------------------|---------------------------|
| Debug Mode      | Always `False`                 | `True`                    |
| Database        | PostgreSQL with connection pool| SQLite                    |
| Error Tracking  | Sentry/DataDog                 | Console output            |
| Static Files    | CDN + WhiteNoise               | Django runserver          |
| Logging         | Structured, rotated logs       | Console output            |

### Pro Tips for Your Guide:

1. **Include Real Examples**:
   ```bash
   # Actual command that worked in your last deployment
   gunicorn --workers=4 --bind=0.0.0.0:8000 core.wsgi
   ```
2. **Add Recovery Procedures:**
## Rollback Process
1. Identify last working commit:
   ```bash
   git log --oneline -n 5
   ```

2. **Rollback:**

```bash 
git checkout <working-commit>
./deploy.sh production
```

### Include Performance Benchmarks:
## Expected Performance
- API Response: <200ms for 95% of requests
- DB Queries: <50ms for 95% of queries
- Concurrent Users: 100+ with 2GB RAM

### Add Maintenance Windows:

## Scheduled Maintenance
- Database backups: Daily at 2AM UTC
- Log rotation: Weekly

### What to Exclude:
- Credentials (use ENV_VAR placeholders)
- Non-reproducible manual steps
- Environment-specific paths (use variables)

### When to Update It:
1. After every production deployment
2. When adding new infrastructure
3. After resolving production issues

