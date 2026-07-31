## Crypto Scheduler (TODO-C1)

### پیاده‌سازی در backend/app/main.py

```python
# اضافه کردن scheduler job برای 6 ساعته

scheduler.register_job(
    name="crypto_fundamental_refresh",
    coroutine_func=crypto_fundamental_service.ingest_data,
    interval_seconds=21600  # 6 ساعت
)

# Hasta این servicios participates
from app.services.analysis.crypto_fundamental_service import CryptoFundamentalService
cryptofundamental_service = container.get("crypto_fundamental_ingestion")
```

### HomeTeam Changes
- ایجاد `ingest_data` method در `crypto_fundamental_service.py`
-ispatch با cached data خودکار