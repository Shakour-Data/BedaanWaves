# BedaanWaves Incident Response Runbook

## Incident Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | Complete outage | 5 minutes |
| P1 | Major feature unavailable | 15 minutes |
| P2 | Minor issue | 1 hour |
| P3 | Cosmetic issue | 4 hours |

## Immediate Actions

1. **Acknowledge incident** in incident channel
2. **Assess impact** - check `/health` endpoint
3. **Notify on-call** via PagerDuty if P0/P1
4. **Create incident log** with timeline

## Common Incidents

### High Latency
1. Check database query performance
2. Check cache hit rate
3. Scale up application replicas
4. Check external API response times

### 5xx Errors
1. Check application logs
2. Check database connection pool
3. Restart affected pods
4. Check circuit breaker state

### Data Freshness Issues
1. Check ingestion pipeline
2. Verify external API availability
3. Check scheduler service
4. Manually trigger data refresh

## Communication Template

```
**Incident Update** [TIME]
**Status:** [ACTIVE/RESOLVED]
**Severity:** [P0/P1/P2/P3]
**Impact:** [description]
**Root Cause:** [if known]
**Resolution:** [steps taken]
**ETA:** [if ongoing]
```

## Post-Incident
1. Document timeline
2. Identify root cause
3. Create action items
4. Update runbooks if needed