# UML Level 5 — Core Domain Classes / Schemas

این سطح کلاس‌ها/اسکیماهای کلیدی را دسته‌بندی می‌کند.

> توجه: برای دقت ۱۰۰٪ باید فایل‌های `app/models/models.py` و `app/schemas/schemas.py` خوانده شوند. در این مرحله بر اساس routeها و architecture موجود، موجودیت‌های اصلی infer شده‌اند.

## Diagram (PlantUML)
```plantuml
@startuml
skinparam classAttributeIconSize 0

class Asset {
  id: UUID
  symbol: str
  name: str
  asset_class: str
  market: str
  sector: str
  industry: str
  active: bool
}

class PriceCandle {
  id: UUID
  asset_id: UUID
  timestamp: datetime
  timeframe: str
  open: decimal
  high: decimal
  low: decimal
  close: decimal
  volume: bigint
}

class MLSignal {
  id: UUID
  asset_id: UUID
  signal_type: str
  confidence: decimal
  expected_return: decimal
  risk_score: decimal
  reasoning: text
  technical_factors: JSON
  fundamental_factors: JSON
  sentiment_factors: JSON
  ml_model_version: str
  is_active: bool
  generated_at: datetime
  valid_until: datetime
}

class Portfolio {
  id: UUID
  user_id: UUID
  name: str
  portfolio_type: str
  base_currency: str
  created_at: datetime
  updated_at: datetime
}

class Position {
  id: UUID
  portfolio_id: UUID
  asset_id: UUID
  quantity: decimal
  entry_price: decimal
  entry_date: date
  stop_loss: decimal
  take_profit: decimal
  notes: text
}

class User {
  id: UUID
  username: str
  email: str
  is_active: bool
  is_admin: bool
}

class Notification {
  id: UUID
  user_id: UUID
  asset_id: UUID?
  is_read: bool
  is_active: bool
  triggered_at: datetime
  payload: JSON?
}

Asset "1" -- "many" PriceCandle
Asset "1" -- "many" MLSignal
User "1" -- "many" Portfolio
Portfolio "1" -- "many" Position
User "1" -- "many" Notification
Asset "1" -- "many" Notification : optional link

@enduml
```

## Mapping to Routes
- `/market/*` روی `Asset` و `PriceCandle`
- `/analysis/*` به خصوص `PriceCandle` + `MLSignal`
- `/portfolios/*` روی `Portfolio` و `Position`
- `/notifications*` روی `Notification` (+ user_id via `get_route_user_id`)
