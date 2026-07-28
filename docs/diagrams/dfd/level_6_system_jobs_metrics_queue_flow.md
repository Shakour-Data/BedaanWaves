# DFD Level 6 — System Jobs, Scheduler, Metrics & Queue Flow

این سطح جریان داده‌ها برای ماژول سیستم را نشان می‌دهد:
- Scheduler: ثبت/لغو/Run job
- Queue: enqueue/get job status/stats/dead-letter
- Metrics: get /metrics و health summary

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend/Admin] --> SCHED1[GET /system/scheduler/jobs]
  FE --> SCHED2[POST /system/scheduler/jobs]
  FE --> SCHED3[POST /system/scheduler/jobs/{name}/run]
  FE --> QUEUE1[POST /system/queue/jobs]
  FE --> QUEUE2[GET /system/queue/jobs/{job_id}]
  FE --> QUEUE3[GET /system/queue/stats]
  FE --> QUEUE4[GET /system/queue/dead-letter]
  FE --> MET1[GET /system/metrics]
  FE --> MET2[GET /system/metrics/health]

  subgraph System[System Services]
    SCH[SchedulerService]
    Q[QueueService]
    M[MetricsService]
  end

  SCHED1 --> SCH
  SCHED2 --> SCH
  SCHED3 --> SCH
  QUEUE1 --> Q
  QUEUE2 --> Q
  QUEUE3 --> Q
  QUEUE4 --> Q

  MET1 --> M
  MET2 --> M

  subgraph DB[(PostgreSQL)]
    AUDIT[optional audit/log tables]
  end

  SCH --> AUDIT
  Q --> AUDIT
  M --> AUDIT
```

## Data Flows
- Job payload و status در QueueService مدیریت می‌شود
- Scheduler jobs در SchedulerService نگهداری/اجرا می‌شوند
- Metrics/health از MetricsService جمع‌آوری می‌شوند

