# UML Level 6 — End-to-End Paths (Request → Middleware → Service → DB/Upstream)

این سطح چند مسیر واقعی را از perspective UML تشریح می‌کند.

## مسیر A: GET /api/v1/market/symbols
```plantuml
@startuml
actor Client
participant "FastAPI App\nmain.py" as APP
participant "CorrelationIdMiddleware" as MID1
participant "RateLimitMiddleware" as MID2
participant "AuthGuardMiddleware (optional)" as MID3
participant "market router\n/market/symbols" as R
participant "DB (Async SQLAlchemy)" as DB
participant "Asset table" as T

Client -> APP : Request GET /api/v1/market/symbols
APP -> MID1 : attach X-Correlation-ID
APP -> MID2 : rate window check
APP -> MID3 : JWT guard if enabled
APP -> R : call get_symbols()
R -> DB : select Asset with filters + offset/limit
DB --> R : assets list
R --> APP : List[AssetResponse]
APP --> Client : 200 JSON
@enduml
```

## مسیر B: GET /api/v1/analysis/technical/{symbol}
```plantuml
@startuml
actor Client
participant "FastAPI App" as APP
participant "middleware chain" as MID
participant "analysis router\n/technical/{symbol}" as R
participant "TechnicalAnalysisService" as S
participant "PostgreSQL" as DB

Client -> APP : GET /api/v1/analysis/technical/FSPD
APP -> MID : correlation/rate/auth
APP -> R : call technical_analysis(symbol)
R -> DB : select Asset by symbol
DB --> R : Asset
R -> DB : select PriceCandle (daily) ordered asc
DB --> R : candles[]
R -> S : initialize + analyze(prices, volumes)
S --> R : indicators (dict)
R --> APP : JSON response
APP --> Client : 200
@enduml
```

## مسیر C: POST /api/v1/portfolios/{portfolio_id}/holdings
```plantuml
@startuml
actor User
participant "AuthGuardMiddleware" as GUARD
participant "get_route_user_id" as ROUTE_ID
participant "portfolios router\n/add holding" as R
participant "DB" as DB
participant "Position" as POS

User -> R : POST holding
R -> GUARD : decode token / set request.state.user_id (if required)
R -> ROUTE_ID : resolve user_id
R -> DB : validate Portfolio + Asset
R -> DB : check existing Position(portfolio_id, asset_id)
alt duplicate
  DB --> R : Position exists
  R --> User : 400
else insert ok
  R -> DB : insert Position(...)
  DB --> R : new Position created
  R --> User : 200 PositionResponse
end
@enduml
```

## مسیر D: GET /api/v1/market/live/history/{l18} (Upstream Proxy)
```plantuml
@startuml
actor Client
participant "market/live router" as R
participant "BrsApiClient" as BRS
participant "BRS API" as UP

Client -> R : GET /api/v1/market/live/history/{l18}
R -> BRS : get_history(l18)
BRS -> UP : History.php request
UP --> BRS : upstream JSON
BRS --> R : payload
R --> Client : 200 JSON
@enduml
```

## مسیر E: POST /api/v1/system/queue/jobs
```plantuml
@startuml
actor Admin
participant "system router /queue/jobs" as R
participant "QueueService" as Q
participant "Queue store" as STORE

Admin -> R : POST {name,payload,priority,max_retries}
R -> Q : initialize + set_processor + enqueue
Q -> STORE : create job record
STORE --> Q : job_id/status
Q --> R : job_id
R --> Admin : 200 {job_id,name}
@enduml
```

## مسیر F: GET /api/v1/analysis/signals/{symbol}
```plantuml
@startuml
actor Client
participant "analysis router\n/analysis/signals/{symbol}" as R
participant "DB" as DB
participant "MLSignal row" as SIG

Client -> R : GET /api/v1/analysis/signals/FSPD
R -> DB : select Asset by symbol
DB --> R : Asset
R -> DB : select latest active MLSignal
DB --> R : MLSignal (valid)
R --> Client : 200 MLSignalResponse
@enduml
```

