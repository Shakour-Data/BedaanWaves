# BedaanWaves Monitoring & Observability Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing a comprehensive monitoring and observability system for the BedaanWaves platform, targeting a score of 95/100.

## Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional)
- Prometheus, Grafana, ELK Stack, Jaeger installed

## Implementation Steps

### Step 1: Install Dependencies

```bash
cd backend
pip install prometheus_client opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger
```

### Step 2: Configure Prometheus

Copy `monitoring/prometheus/prometheus.yml` to your Prometheus config directory.

### Step 3: Configure Alert Rules

Copy `monitoring/prometheus/rules/alert_rules.yml` to your Prometheus rules directory.

### Step 4: Configure Alertmanager

Copy `monitoring/alertmanager/alertmanager.yml` to your Alertmanager config directory.

### Step 5: Set up Grafana Dashboards

Import the following dashboards into Grafana:
- `monitoring/grafana/dashboards/platform_overview.json`
- `monitoring/grafana/dashboards/developer_dashboard.json`

### Step 6: Configure ELK Stack

1. Copy `monitoring/elk/filebeat.yml` to your Filebeat config directory
2. Copy `monitoring/elk/logstash.conf` to your Logstash config directory
3. Set up Elasticsearch and Kibana with the BedaanWaves index pattern

### Step 7: Configure Jaeger

Copy `monitoring/jaeger/jaeger.yaml` to your Jaeger config directory.

### Step 8: Update Service Registration

Update `backend/app/main.py` to register the new services:

```python
from app.services.system import (
    HealthCheckService,
    TracingService,
    IncidentResponseService,
    SelfHealingService,
)

# In lifespan:
health_check_service = HealthCheckService()
tracing_service = TracingService()
incident_response_service = IncidentResponseService()
self_healing_service = SelfHealingService()

# Register services
container.register("health_check", health_check_service)
container.register("tracing", tracing_service)
container.register("incident_response", incident_response_service)
container.register("self_healing", self_healing_service)
```

### Step 9: Add Health Check Endpoints

Update `backend/app/api/routes/` to add health check endpoints:

```python
from fastapi import APIRouter
from app.services.system import HealthCheckService

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/liveness")
async def liveness_check():
    return await health_check_service.check_liveness()

@router.get("/readiness")
async def readiness_check():
    return await health_check_service.check_readiness()

@router.get("/health")
async def health_check():
    return await health_check_service.check_health()
```

### Step 10: Add Metrics Endpoint

```python
@router.get("/metrics")
async def metrics():
    return metrics_service.render_prometheus()
```

### Step 11: Run Verification

```bash
cd backend
python -m pytest app/tests/ -v
```

## Verification Checklist

- [ ] Prometheus is collecting metrics from all services
- [ ] Grafana dashboards are displaying data correctly
- [ ] Alertmanager is receiving and routing alerts
- [ ] Filebeat is shipping logs to Elasticsearch
- [ ] Jaeger is receiving traces
- [ ] Health check endpoints are responding correctly
- [ ] Self-healing is working for critical services
- [ ] Incident response is triggered for critical alerts

## Expected Score: 95/100

## Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| API Error Rate | < 1% | > 5% |
| 95th Percentile Latency | < 500ms | > 1s |
| CPU Usage | < 70% | > 90% |
| Memory Usage | < 70% | > 90% |
| Disk Usage | < 80% | > 90% |
| Cache Hit Rate | > 80% | < 60% |

## Runbook Links

- High Error Rate: https://docs.bedaanwaves.com/runbooks/high-error-rate
- High Latency: https://docs.bedaanwaves.com/runbooks/high-latency
- Low Disk Space: https://docs.bedaanwaves.com/runbooks/low-disk-space
- Service Down: https://docs.bedaanwaves.com/runbooks/service-down