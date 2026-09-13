# Disaster Recovery Runbook

## Overview

This runbook describes the disaster recovery procedures for BedaanWaves.

**RTO:** 15 minutes  
**RPO:** 5 minutes  
**Primary Region:** us-east-1  
**Replica Region:** us-west-2

---

## Scenario 1: Database Failure

### Detection
- Health check `/health` returns `degraded`
- Database connection errors in logs
- Alerts from Prometheus

### Recovery Steps

1. **Verify the failure**
   ```bash
   curl https://api.bedaanwaves.com/health
   ```

2. **Check database status**
   ```bash
   kubectl logs -l app=bedaanwaves,tier=db=core -f
   ```

3. **Attempt automatic recovery**
   - Self-HealingService will attempt restart
   - Wait 2 minutes

4. **If automatic recovery fails, trigger manual failover**
   ```bash
   curl -X POST https://api.bedaanwaves.com/api/v1/system/dr/failover \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"reason": "database_failure"}'
   ```

5. **Verify failover**
   ```bash
   curl https://api.bedaanwaves.com/health
   ```

---

## Scenario 2: Application Failure

### Detection
- 5xx errors in logs
- High latency
- Health check failures

### Recovery Steps

1. **Check application logs**
   ```bash
   kubectl logs -l app=bedaanwaves,tier=backend -f
   ```

2. **Restart application**
   ```bash
   kubectl rollout restart deployment/bedaanwaves-backend
   ```

3. **Verify recovery**
   ```bash
   curl https://api.bedaanwaves.com/health
   ```

---

## Scenario 3: Complete Region Failure

### Detection
- All health checks fail
- External monitoring alerts
- DNS resolution failures

### Recovery Steps

1. **Verify region failure**
   - Check external monitoring
   - Verify DNS resolution

2. **Initiate DR failover**
   ```bash
   curl -X POST https://api.bedaanwaves.com/api/v1/system/dr/failover \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"reason": "region_failure"}'
   ```

3. **Verify failover**
   ```bash
   curl https://api.bedaanwaves.com/health
   ```

4. **Notify stakeholders**
   - Send incident notification
   - Update status page
   - Communicate ETA

---

## Scenario 4: Data Corruption

### Detection
- Data integrity check failures
- Unexpected data patterns
- Manual reports

### Recovery Steps

1. **Identify corruption scope**
   ```bash
   curl https://api.bedaanwaves.com/api/v1/system/data-integrity/check
   ```

2. **Restore from backup**
   ```bash
   curl -X POST https://api.bedaanwaves.com/api/v1/system/backup/restore \
     -H "Authorization: Bearer $ADMIN_TOKEN" \
     -d '{"backup_id": "latest"}'
   ```

3. **Verify data integrity**
   ```bash
   curl https://api.bedaanwaves.com/api/v1/system/data-integrity/check
   ```

---

## Backup Schedule

| Type | Schedule | Retention |
|------|----------|-----------|
| Full | Daily 02:00 UTC | 30 days |
| Incremental | Every 6 hours | 7 days |
| WAL | Continuous | 2 days |

## Backup Verification

- Daily automated restore test
- Weekly full restore test
- Monthly DR drill

---

## Contact

- **On-call Engineer:** Check PagerDuty rotation
- **Database Admin:** DBA team Slack channel
- **Infrastructure:** Platform team Slack channel