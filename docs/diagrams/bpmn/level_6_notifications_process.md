# BPMN Level 6 — Notifications Process

این سطح فرآیند اطلاع‌رسانی را بر اساس routeهای موجود نشان می‌دهد:
- `GET /notifications?unread_only&limit&offset`
- `POST /notifications/{notification_id}/read`
- `POST /notifications/read-all`
- `DELETE /notifications/{notification_id}`

> توجه: تولید notification (Triggerها) در کد route این فایل دیده نمی‌شود. اما روند “مدیریت وضعیت و نمایش” کاملاً از روی routes مشخص است.

## Diagram (Mermaid)
```mermaid
flowchart TD
  FE[Frontend] --> L1[GET /api/v1/notifications]
  L1 --> AUTH[AuthGuard + get_route_user_id]
  AUTH --> DB[(DB: notifications)]
  DB --> L1
  L1 --> FE

  FE --> M1[POST /api/v1/notifications/{id}/read]
  M1 --> AUTH
  AUTH --> DB
  DB --> M2[mark_read]
  M2 --> DB
  M2 --> M1
  M1 --> FE

  FE --> A1[POST /api/v1/notifications/read-all]
  A1 --> AUTH
  AUTH --> DB
  DB --> A2[mark_all_read]
  A2 --> A1
  A1 --> FE

  FE --> D1[DELETE /api/v1/notifications/{id}]
  D1 --> AUTH
  AUTH --> DB
  DB --> D2[delete_notification]
  D2 --> D1
  D1 --> FE
```

## داده‌ها/ایونت‌ها
- `NotificationResponse`: اطلاعات notification برای نمایش
- عملیات‌های DB:
  - `mark_read(notification_id,user_id)`
  - `mark_all_read(user_id)`
  - `delete_notification(notification_id,user_id)`

