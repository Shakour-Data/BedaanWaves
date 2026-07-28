# UML Level 4 — Sequence Diagrams (Key Scenarios)

این سطح سناریوهای کلیدی Sequence را نشان می‌دهد.

## 1) Login (Public endpoint)
```plantuml
@startuml
actor User
participant "Frontend" as FE
participant "Backend /auth/login" as R
participant "Auth Service" as AUTH
participant "PostgreSQL" as DB

User -> FE : POST /api/v1/auth/login\n(username,password)
FE -> R : request body
R -> AUTH : authenticate_user(username,password)
AUTH -> DB : select User by username
DB --> AUTH : user row
AUTH --> R : user or None
alt success
  R -> R : create_access_token/create_refresh_token
  R --> FE : 200 Token(access,refresh)
else failure
  R --> FE : 401 Incorrect username or password
end
@enduml
```

## 2) Get ML Signal (Protected)
```plantuml
@startuml
actor User
participant "Frontend" as FE
participant "Middleware Chain\nCorrelation/Rate/AuthGuard" as MID
participant "Router /analysis/signals/{symbol}" as R
participant "DB (AsyncSession)" as DB
participant "MLSignal model" as MS

User -> FE : GET /api/v1/analysis/signals/FSPD\nAuthorization: Bearer ...
FE -> MID : Request
MID -> R : next()
R -> DB : select Asset by symbol
DB --> R : Asset
R -> DB : select latest active MLSignal\nwhere valid_until >= now
DB --> R : MLSignal row
R --> FE : 200 MLSignalResponse
@enduml
```

## 3) Add Holding to Portfolio (Protected)
```plantuml
@startuml
actor User
participant "Frontend" as FE
participant "AuthGuard + get_route_user_id" as AUTH
participant "Router /portfolios/{id}/holdings" as R
participant "DB" as DB

User -> FE : POST /api/v1/portfolios/{pid}/holdings\nAuthorization: Bearer ...
FE -> AUTH : middleware resolves request.state.user_id
AUTH --> R : user_id
R -> DB : load Portfolio(portfolio_id)
DB --> R : portfolio or None
R -> DB : load Asset(asset_id)
DB --> R : asset
R -> DB : check existing Position(portfolio_id, asset_id)
DB --> R : exists/None
alt exists
  R --> FE : 400 Holding already exists
else ok
  R -> DB : insert Position(...)
  DB --> R : Position created
  R --> FE : 200 PositionResponse
end
@enduml
```

## 4) Live Candlestick Proxy (Upstream)
```plantuml
@startuml
actor User
participant "Frontend" as FE
participant "Router /market/live/candlestick/{l18}" as R
participant "BRS BrsApiClient" as BRS

User -> FE : GET /api/v1/market/live/candlestick/{l18}
FE -> R : request
R -> BRS : get_candlestick(l18, candle_type)
BRS --> R : upstream JSON payload
R --> FE : 200 upstream response
@enduml
```

## 5) Enqueue system job
```plantuml
@startuml
actor Admin
participant "Frontend" as FE
participant "Router /system/queue/jobs" as R
participant "QueueService" as Q

Admin -> FE : POST /api/v1/system/queue/jobs\n{name,payload,priority,max_retries}
FE -> R : JSON body
R -> Q : enqueue(name,payload,priority,max_retries)
Q --> R : job_id
R --> FE : 200 {job_id,name}
@enduml
