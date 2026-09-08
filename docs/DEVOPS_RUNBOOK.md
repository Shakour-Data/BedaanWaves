# BedaanWaves DevOps Runbook

## 1. Deployment Procedures

### 1.1 Production Deployment (Blue-Green)
```bash
# 1. Build artifact
tar -czf bedaanwaves-${COMMIT_SHA}.tar.gz -C deploy-package .

# 2. Deploy via Ansible
ansible-playbook -i inventory/production.ini playbooks/deploy.yml --tags deploy

# 3. Verify health
curl -sf http://localhost:3000/api/v1/health

# 4. Switch traffic
sudo systemctl reload nginx
```

### 1.2 Rollback Procedure
```bash
# Emergency rollback
sudo systemctl stop bedaanwaves-production
ln -sfn /opt/bedaanwaves/production/blue/releases/previous \
       /opt/bedaanwaves/production/active
sudo systemctl start bedaanwaves-production
sudo systemctl reload nginx
```

### 1.3 Database Migration
```bash
cd /opt/bedaanwaves/production/current/backend
source venv/bin/activate
alembic upgrade head
```

## 2. Monitoring & Alerting

### 2.1 Access Dashboards
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Alertmanager: http://localhost:9093

### 2.2 Key Metrics
- API latency p95: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
- Error rate: `sum(rate(http_requests_total{status_code=~"5.."}[1m]))`
- CPU usage: `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- Memory usage: `100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))`

### 2.3 Alert Response
1. **High CPU/Memory**: Check process list, restart service if needed
2. **Service Down**: Check systemd status, review logs, restart
3. **Database Down**: Check PostgreSQL status, verify connections
4. **High Error Rate**: Check application logs, verify recent deploy

## 3. Log Management

### 3.1 Access Logs
```bash
# Application logs
tail -f /opt/bedaanwaves/production/current/backend/logs/app.log

# System logs
journalctl -u bedaanwaves-production -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 3.2 Centralized Logging
- Kibana: http://localhost:5601
- Index pattern: `filebeat-*`
- Time field: `@timestamp`

## 4. Security Procedures

### 4.1 SSH Access
```bash
# Connect to production
ssh -i ~/.ssh/bedaanwaves_deploy bedaanwaves@prod-server-1

# Bastion host
ssh -i ~/.ssh/bedaanwaves_deploy -J bastion bedaanwaves@prod-server-1
```

### 4.2 Secret Rotation
```bash
# Rotate JWT secret
export JWT_SECRET=$(openssl rand -base64 64)
sudo systemctl restart bedaanwaves-production
```

### 4.3 Security Updates
```bash
# Automated via unattended-upgrades
# Manual update
sudo apt update && sudo apt upgrade -y
sudo systemctl restart bedaanwaves-production
```

## 5. Backup & Recovery

### 5.1 Database Backup
```bash
# Daily backup
pg_dump -U bedaanwaves bedaanwaves_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup_20240908.sql.gz | psql -U bedaanwaves bedaanwaves_db
```

### 5.2 Disaster Recovery
```bash
# Spin up DR environment
cd deployment/terraform
terraform apply -var-file=dr.tfvars

# Restore from backup
ansible-playbook -i inventory/dr.ini playbooks/restore.yml
```

## 6. Troubleshooting

### 6.1 Service Won't Start
```bash
# Check status
sudo systemctl status bedaanwaves-production

# Check logs
journalctl -u bedaanwaves-production -n 100

# Check port conflicts
sudo lsof -i :3000
```

### 6.2 Database Connection Issues
```bash
# Test connection
psql -U bedaanwaves -h localhost -p 5432 bedaanwaves_db

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### 6.3 High Load
```bash
# Check processes
top -u bedaanwaves
htop

# Check connections
ss -tulpn | grep :3000

# Rate limit check
sudo fail2ban-client status sshd
```

## 7. Maintenance Windows

- **Scheduled**: Sundays 02:00-06:00 UTC
- **Emergency**: As needed with 15min notice
- **Rollback SLA**: < 5 minutes
- **Max downtime**: 30 minutes planned

## 8. Escalation Matrix

| Severity | Response Time | Escalation |
|----------|--------------|------------|
| P1 (Critical) | 15 min | On-call + VP Engineering |
| P2 (High) | 1 hour | On-call |
| P3 (Medium) | 4 hours | DevOps team |
| P4 (Low) | Next business day | DevOps team |
