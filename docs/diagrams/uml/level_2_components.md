# UML Level 3 — Service Decomposition (Domain Services)

این سطح سرویس‌ها را به حوزه‌های Domain تقسیم می‌کند.

## حوزه‌ها
- **Auth / User**
- **Market / Data Access**
- **Analysis**
- **Portfolio / Risk-aware operations**
- **ML**
- **System / Queue / Scheduler / Metrics**
- **Notifications**

## Diagram (PlantUML)
```plantuml
@startuml
skinparam componentStyle rectangle

package "Auth / User" {
  [auth_service.py] as AUTH_S
  [authorization_service] as AUTHZ_S
  [user_profile_service] as PROFILE_S
  [watchlist_service] as WATCH_S
  [notification_service] as NOTIF_S
  [preference_service] as PREF_S
}

package "Market / Data Access" {
  [BrsApiClient] as BRS_CLIENT
  [StockService] as STOCK_S
  [MarketService] as MARKET_S
  [HistoryService] as HISTORY_S
  [NewsService] as NEWS_S
}

package "Analysis" {
  [TechnicalAnalysisService] as TECH_S
  [FundamentalAnalysisService] as FUND_S
  [MomentumService] as MOM_S
  [VolatilityService] as VOL_S
  [RiskAnalysisService] as RISK_S
  [ScoringService] as SCORE_S
}

package "ML" {
  [PredictionService] as PRED_S
  [PatternRecognitionService] as PAT_S
  [AnomalyDetectionService] as ANOM_S
  [RecommendationService] as REC_S
  [PortfolioOptimizationService] as OPT_S
  [TimeSeriesForecastingService] as TSF_S
}

package "System" {
  [SchedulerService] as SCH_S
  [QueueService] as QUEUE_S
  [MetricsService] as METR_S
}

[FastAPI Routers] --> [Auth / User] : calls via service
[FastAPI Routers] --> [Market / Data Access] : data fetch/normalize
[FastAPI Routers] --> [Analysis] : compute indicators/scores
[FastAPI Routers] --> [ML] : predict/recommend/forecast
[FastAPI Routers] --> [System] : jobs/metrics/queue
[FastAPI Routers] --> [Auth / User] : notifications + user-owned ops

[Analysis] --> [PostgreSQL] : candles/assets/signal tables
[Market / Data Access] --> [PostgreSQL] : assets + price_candles
[ML] --> [PostgreSQL] : candles -> features -> results
[Auth / User] --> [PostgreSQL] : user/roles/notifications

[Market / Data Access] --> [BRS API] : upstream requests
[ML] --> [PostgreSQL] : store ML results
[FastAPI Routers] --> [System] : enqueue/run jobs

@enduml
```

## نکته
- برخی routeها (مثل `live/*`) مستقیم proxy به BRS API هستند و DB لازم ندارند.
- برخی routeها (مثل `/analysis/technical/{symbol}`) از داده‌های stored در DB استفاده می‌کنند.
