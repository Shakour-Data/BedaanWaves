# BedaanWaves Server Specifications

## Overview
This document outlines the recommended server specifications for deploying BedaanWaves in production environments, based on analysis of the system architecture, data storage requirements, and performance considerations.

## Hardware Specifications

### Minimum Requirements (Development/Testing)
| Component | Specification | Notes |
|-----------|---------------|-------|
| CPU | 4 cores (modern x86_64) | Intel i5/Ryzen 5 equivalent |
| RAM | 8 GB | Suitable only for development/testing |
| Storage | 50 GB SSD | For OS, application, and small datasets |
| Network | 1 Gbps | Basic connectivity |

### Recommended Production Specifications
| Component | Specification | Notes |
|-----------|---------------|-------|
| CPU | 8-16 cores (modern x86_64) | Intel Xeon/Epyc or equivalent |
| RAM | **64-128 GB** | Based on data volume and concurrency |
| Storage | **256 GB - 2 TB NVMe SSD** | For database, logs, and temporary files |
| Network | 10 Gbps | For high-volume data ingestion |

### Optimal Specifications for Large Deployments
| Component | Specification | Notes |
|-----------|---------------|-------|
| CPU | 16-32 cores | For high-concurrency scenarios |
| RAM | **128-256 GB** | For large datasets (>500 GB) and caching |
| Storage | **2-4 TB NVMe SSD** (RAID 10) | High I/O for time-series data |
| Network | 10-25 Gbps | For distributed deployments |

## Software Requirements

### Operating System
- **Recommended:** Ubuntu 22.04 LTS or later, RHEL 9, or CentOS Stream 9
- **Minimum:** Any modern Linux distribution with kernel 5.4+
- **Not Supported:** Windows Server (for production)

### Runtime Dependencies
| Component | Version | Installation Method |
|-----------|---------|---------------------|
| Python | 3.11+ | From official repositories or pyenv |
| PostgreSQL | 13+ | Official packages or PGDG repository |
| Redis | 6+ | Official packages |
| Node.js | 18+ LTS | For frontend build (if self-hosted) |
| npm/yarn | Latest | For frontend dependencies |

### Additional Tools
- Git (for version control)
- curl/wget (for health checks)
- jq (for JSON processing)
- htop/glances (for monitoring)
- logrotate (for log management)

## Database Specifications

### PostgreSQL Configuration
| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| shared_buffers | 25% of RAM | Max 32GB on systems with >128GB RAM |
| effective_cache_size | 75% of RAM | OS + PostgreSQL cache |
| work_mem | 64MB | Per operation, adjust based on concurrency |
| maintenance_work_mem | 2GB | For VACUUM, CREATE INDEX |
| max_connections | 100-200 | Depends on application pool size |
| wal_buffers | 16MB | For write-heavy workloads |
| checkpoint_timeout | 15min | Balance recovery time vs. I/O |
| max_wal_size | 2GB | Adjust based on write volume |
| min_wal_size | 800MB | |

### Storage Layout
- **Data Directory:** Dedicated mount point with noatime,nodiratime options
- **WAL Directory:** Separate high-performance storage if possible
- **Backup Storage:** Separate volume or remote storage
- **Tablespace:** Consider separate tablespaces for indexes if beneficial

### Partitioning Strategy
- **Raw Data:** Monthly partitions (retention 90 days)
- **Processed Data:** No partitioning (indefinite retention)
- **Time-Series Tables:** Daily or hourly partitions for high-frequency data
- **Archive Strategy:** Move old partitions to cheaper storage

## Redis Configuration
| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| maxmemory | 40-60% of total RAM | Leave room for OS and PostgreSQL |
| maxmemory-policy | allkeys-lru | Evict least recently used keys |
| save | 900 1, 300 10, 60 10000 | RDB snapshots |
| appendonly | yes | Enable AOF for durability |
| appendfsync | everysec | Balance performance vs. durability |

## Application Configuration
| Setting | Recommended Value | Notes |
|---------|-------------------|-------|
| Workers (Uvicorn) | 2-4 x CPU cores | Adjust based on load testing |
| Worker Class | uvicorn.workers.UvicornWorker | For async support |
| Keep Alive | 5-15 seconds | Tune based on client behavior |
| Timeout | 30-60 seconds | For long-running requests |
| Max Requests | 1000 | Worker recycling to prevent leaks |

## Network & Security

### Firewall Rules
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Admin IPs only | SSH |
| 80 | TCP | 0.0.0.0/0 | HTTP (redirect to HTTPS) |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 5432 | TCP | App servers only | PostgreSQL |
| 6379 | TCP | App servers only | Redis |
| 9090 | TCP | Monitoring only | Prometheus |
| 3000 | TCP | Monitoring only | Grafana |

### TLS/SSL
- **Certificate:** Let's Encrypt or commercial CA
- **Protocols:** TLS 1.2+, prefer TLS 1.3
- **Cipher Suites:** Modern secure configuration
- **HSTS:** Enable with max-age=31536000
- **OCSP Stapling:** Enable for performance

## Monitoring & Logging

### Metrics Collection
- **Prometheus:** Scrape application metrics at `/metrics`
- **Node Exporter:** Host-level metrics
- **PostgreSQL Exporter:** Database metrics
- **Redis Exporter:** Cache metrics

### Logging
| Log Type | Destination | Retention | Level |
|----------|-------------|-----------|-------|
| Application | Centralized (ELK/Loki) | 30 days | INFO |
| Error | Centralized | 90 days | ERROR |
| Access | Centralized | 7 days | INFO |
| Audit | Centralized | 365 days | INFO |
| System | Local + Remote | 30 days | varies |

### Health Checks
- **Endpoint:** `/health` (returns 200 when healthy)
- **Depth:** Checks DB, cache, and critical services
- **Frequency:** Every 30 seconds
- **Timeout:** 5 seconds

## Scaling Considerations

### Vertical Scaling Limits
- **RAM:** Practical limit ~512GB for single server
- **CPU:** Diminishing returns beyond 32 cores for this workload
- **Storage:** NVMe SSD limits ~8TB practical for single server

### Horizontal Scaling Options
1. **Read Replicas:** For distributing read queries
2. **Application Sharding:** By market type or user region
3. **Microservices:** Split services by function (already partially implemented)
4. **CDN:** For frontend static assets

### Capacity Planning Triggers
| Metric | Threshold | Action |
|--------|-----------|--------|
| RAM Usage | >85% sustained | Plan upgrade |
| CPU Usage | >75% sustained | Consider scaling |
| Disk Usage | >80% | Cleanup or expand storage |
| DB Connections | >80% max | Increase pool or connections |
| Replication Lag | >5s | Investigate replica health |

## Backup & Disaster Recovery

### Backup Strategy
- **Full Backup:** Daily at 02:00 UTC
- **Incremental:** Every 4 hours
- **WAL Archiving:** Continuous
- **Retention:** 30 days full, 90 days incremental

### Recovery Objectives
- **RPO:** < 15 minutes (WAL replay)
- **RTO:** < 60 minutes for full restore
- **Test Frequency:** Monthly restore tests

### Disaster Recovery Site
- **Async Replication:** To secondary site
- **Failover Time:** < 5 minutes with proper orchestration
- **Regular Drills:** Quarterly DR exercises

## Implementation Checklist

### Pre-Deployment
- [ ] Provision hardware according to specifications
- [ ] Install and configure OS with security hardening
- [ ] Set up monitoring and alerting
- [ ] Configure backup systems
- [ ] Establish security baseline

### Database Setup
- [ ] Install PostgreSQL with recommended settings
- [ ] Create database and user with least privileges
- [ ] Implement partitioning strategy
- [ ] Configure streaming replication (if HA needed)
- [ ] Set up backup and WAL archiving

### Application Deployment
- [ ] Install Python dependencies in virtual environment
- [ ] Configure environment variables securely
- [ ] Set up systemd services for application workers
- [ ] Configure reverse proxy (nginx/caddy)
- [ ] Install and configure Redis

### Validation
- [ ] Run deployment checklist from docs/deployment_checklist.md
- [ ] Execute integration test suite
- [ ] Verify end-to-end workflows:
  - Data ingestion pipeline
  - Fundamental analysis calculation
  - ML prediction endpoint
  - User authentication flow
- [ ] Confirm no failed tests or warnings

## Maintenance Windows

- **Weekly:** Log rotation, temporary file cleanup
- **Monthly:** Database vacuum analyze, backup verification
- **Quarterly:** Hardware diagnostics, firmware updates
- **Annually:** Capacity review, disaster recovery test

## Appendix: Sample System Configuration

### /etc/sysctl.conf (Performance Tuning)
```conf
# Network optimizations
net.core.somaxconn = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.ip_local_port_range = 1024 65535

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.overcommit_memory = 1

# File system
fs.file-max = 655350
fs.inotify.max_user_watches = 524288
```

### PostgreSQL postgresql.conf Sample
```conf
# Memory
shared_buffers = 24GB
effective_cache_size = 72GB
work_mem = 64MB
maintenance_work_mem = 2GB
temp_file_limit = 10GB

# Connections
max_connections = 200
superuser_reserved_connections = 3

# WAL
wal_buffers = 16MB
checkpoint_timeout = 15min
max_wal_size = 2GB
min_wal_size = 800MB
wal_compression = on
wal_log_hints = on

# Checkpoints
checkpoint_completion_target = 0.9
max_worker_processes = 8
max_parallel_workers_per_gather = 2
max_parallel_workers = 4

# Logging
log_line_format = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_min_duration_statement = 500ms
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 0
log_autovacuum_min_duration = 0
```

This specification document should be reviewed and updated annually or when significant changes occur in the system architecture or usage patterns.