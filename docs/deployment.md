# BedaanWaves Deployment Documentation

## Environment Requirements
- Python 3.11+ runtime
- PostgreSQL 14+ database server
- Redis (optional cache layer)
- Backup storage for database files
- Minimum 8GB RAM, 4 CPU cores

## Deployment Process

### 1. Environment Setup
- Install Python dependencies: `pip install -r requirements.txt`
- Configure `.env` file with production secrets
- Initialize database: `createdb bedaanwaves`
- Apply migrations: `alembic upgrade head`

### 2. Backend Deployment
- Start PostgreSQL with production parameters
- Launch backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Verify health status: `GET /health`

### 3. Frontend Deployment
- Build Next.js app: `npm run build`
- Serve static files via Nginx/Apache or Node server

### 4. Database Configuration
- Set database credentials in `.env`
- Enable replicas if needed

### 5. Security Configuration
- Set up SSL termination in web server
- Configure firewall rules
- Enable rate limiting

## Maintenance Procedures
- Daily backups via `backup_service`
- Monthly security audits
- Performance monitoring through Prometheus
- Scheduled cache invalidations

## Rollback Strategy
1. Restore latest backup
2. Reapply pending migrations
3. Rebuild from last known good state

---

## Deployment Checklist

### Pre-Deployment

- [ ] Verify production environment requirements:
  - Python 3.11+
  - PostgreSQL 13+ running on dedicated server (NOT local)
  - Redis 6+ for caching and background tasks
  - Sufficient memory (≥ 2GB, recommended ≥ 4GB)

- [ ] Configure environment variables:
  - Set `ENVIRONMENT=production`
  - Set appropriate `LOG_LEVEL=info` or `warning`
  - Use strong `JWT_SECRET` (at least 32 random characters)
  - Configure email/SMS notification providers
  - Set up monitoring endpoints

- [ ] Security hardening:
  - Enable HTTPS termination at reverse proxy (nginx/caddy)
  - Configure rate limiting (max 100 requests/ip/5m)
  - Set up CORS restrictions to approved domains
  - Configure security headers (HSTS, CSP, X-Frame-Options)
  - Enable SSL certificate (Let's Encrypt or commercial)

- [ ] Database preparation:
  - Run migrations: `alembic upgrade head`
  - Optimize database indexes
  - Configure read replicas (optional for high availability)
  - Set up automated backups (daily snapshots)

- [ ] Infrastructure setup:
  - Provision server(s) with auto-scaling groups
  - Configure load balancer (nginx/caddy/ALB)
  - Set up monitoring (Prometheus + Grafana)
  - Enable alerting for service health metrics
  - Configure log aggregation (ELK stack or similar)

### Deployment Steps

1. **Backend Deployment**
   - [ ] Pull latest master branch
   - [ ] Install dependencies: `pip install -r requirements.txt`
   - [ ] Apply database migrations: `alembic upgrade head`
   - [ ] Set environment variables in secure way (not committed to repo)
   - [ ] Start backend server with production config:
     ```bash
     uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
     ```

2. **Frontend Deployment**
   - [ ] Pull latest frontend branch
   - [ ] Run production build: `npm run build`
   - [ ] Serve static files with production server (nginx/caddy)
     ```nginx
     location / {
         root /var/www/bedaanwaves/frontend/build;
         try_files $uri $uri/ /index.html;
     }
     ```
   - [ ] Test frontend functionality with live backend API

3. **Service Registration**
   - [ ] Ensure all services are registered in DependencyContainer
   - [ ] Verify background tasks are properly configured
   - [ ] Test service health endpoints: `/health`, `/metrics`

4. **Testing Verification**
   - [ ] Run integration test suite: `python -m pytest tests/ --tb=short`
   - [ ] Verify end-to-end workflows:
     - Data ingestion pipeline
     - Fundamental analysis calculation
     - ML prediction endpoint
     - User authentication flow
   - [ ] Confirm no failed tests or warnings

### Post-Deployment

- [ ] Monitor deployment logs for errors
- [ ] Perform smoke testing of all API endpoints
- [ ] Verify database connectivity and query performance
- [ ] Check cache functionality for repeated requests
- [ ] Validate rate limiting behavior
- [ ] Confirm notification dispatch works (email/SMS)
- [ ] Verify metrics are being collected properly

### Rollback Plan

1. Stop all running services
2. Restore previous stable database backup
3. Revert to previous deployment version
4. Restart services
5. Verify system functionality

### Monitoring & Alerts

- Track CPU/memory usage of all services
- Monitor request latency (p95 should stay < 300ms)
- Alert on 5xx HTTP errors > 5 per minute
- Alert on failed health checks > 3 per minute
- Track queue depth for background processing
- Record cache hit/miss ratios