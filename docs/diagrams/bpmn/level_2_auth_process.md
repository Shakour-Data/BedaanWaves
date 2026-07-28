# BPMN Level 2 — Authentication Process (Register/Login/Refresh)

این سطح فرآیند احراز هویت را (در حد فرآیندهای API موجود) نشان می‌دهد.

## Diagram (Mermaid)
```mermaid
flowchart TD
  subgraph Public[Public Endpoints]
    A1[Register /auth/register]
    A2[Login /auth/login]
    A3[Refresh /auth/refresh]
  end

  FE[Frontend] --> A1
  FE --> A2
  FE --> A3

  A1 --> S1[create_user + hash_password]
  S1 --> DB1[(PostgreSQL users)]
  DB1 --> A1
  A1 --> T1[JWT Access + Refresh tokens]
  T1 --> FE

  A2 --> S2[authenticate_user]
  S2 --> DB1
  DB1 --> S2
  alt success
    S2 --> T2[JWT Access + Refresh tokens]
    T2 --> FE
  else failure
    S2 --> E401[401 Incorrect username or password]
    E401 --> FE
  end

  A3 --> S3[decode refresh token + validate type=refresh]
  S3 --> DB1
  alt valid
    S3 --> T3[JWT Access + Refresh tokens]
    T3 --> FE
  else invalid
    S3 --> E401b[401 Invalid refresh token]
    E401b --> FE
  end
```

## داده‌ها/ایونت‌ها
- `RegisterRequest`: username, email, full_name, password
- `LoginRequest`: username, password
- `Token`: access_token, refresh_token
- JWT payload: `{sub, user_id, type}`

