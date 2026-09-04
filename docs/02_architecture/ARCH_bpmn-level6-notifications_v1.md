# BPMN Level 6 — Notifications Process

This level shows the notification process based on the available routes:
- `GET /notifications?unread_only&limit&offset`
- `POST /notifications/{notification_id}/read`
- `POST /notifications/read-all`
- `DELETE /notifications/{notification_id}`

> Note: Notification generation (Triggers) is not visible in this file's route code. However, the "status management and display" flow is fully clear from the routes.

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

## Data / Events
- `NotificationResponse`: notification information for display
- DB operations:
  - `mark_read(notification_id,user_id)`
  - `mark_all_read(user_id)`
  - `delete_notification(notification_id,user_id)`