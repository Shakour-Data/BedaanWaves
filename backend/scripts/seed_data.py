"""
Seed Data Script - BedaanWaves
============================================================================
پر می‌کند پایگاه‌داده را با داده‌های نمایشی واقع‌گرایانه:

  - assets:         نمادهای بورس/فرابورس و دارایی‌های دیجیتال
  - price_candles:  کندل‌های روزانه‌ی OHLCV (random-walk)
  - users:          یک کاربر نمایشی
  - portfolios:     یک پورتفولیو با موقعیت‌ها
  - ml_signals:     سیگنال‌های هوشمند
  - alerts:         چند هشدار کاربر

قابلیت اجرای مجدد (Idempotent): پیش از درج، رکوردهای قبلی را پاک می‌کند.

اجرا:
    cd backend
    python scripts/seed_data.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# اطمینان از import شدن بسته‌ی app
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# خروجی UTF-8 (برای نمایش فارسی روی کنسول ویندوز)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# درایور نصب‌شده psycopg (v3) است؛ رشته‌ی اتصال را با آن هم‌رسان.
from dotenv import load_dotenv

load_dotenv(os.path.join(BACKEND_ROOT, ".env"))

# برخی محیط‌ها متغیرهایی مثل DEBUG را روی مقادیر غیرِبولی (مثلاً release)
# تنظیم کرده‌اند که اعتبارسنجی Settings را می‌شکند. پیش از import ماژول‌های app
# آن‌ها را به مقدار معتبر بازنشانی می‌کنیم.
os.environ.setdefault("DEBUG", "True")
os.environ["DEBUG"] = "True"

RAW_URL = os.getenv("DATABASE_URL", "postgresql://postgres:BedaanWaves2026@localhost:5432/bedaanwaves_db")
SEED_URL = RAW_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://")
if SEED_URL.startswith("postgresql://"):
    SEED_URL = SEED_URL.replace("postgresql://", "postgresql+psycopg://", 1)
# base.py در زمان import موتور را با DATABASE_URL می‌سازد
os.environ["DATABASE_URL"] = SEED_URL

from sqlalchemy import create_engine, delete  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models.models import (  # noqa: E402
    Asset,
    PriceCandle,
    MLSignal,
    Portfolio,
    Position,
    User,
    Alert,
    APILog,
)


# ---------------------------------------------------------------------------
# داده‌های پایه
# ---------------------------------------------------------------------------
ASSETS = [
    # symbol, name, asset_class, market, sector, currency
    ("فولاد", "فولاد مبارکه اصفهان", "EQUITY", "TSE", "فلزات اساسی", "IRR"),
    ("فملی", "ملی صنایع مس ایران", "EQUITY", "TSE", "فلزات اساسی", "IRR"),
    ("شستا", "سرمایه‌گذاری تامین اجتماعی", "EQUITY", "TSE", "سرمایه‌گذاری", "IRR"),
    ("خودرو", "ایران خودرو", "EQUITY", "TSE", "خودرو", "IRR"),
    ("وبملت", "بانک ملت", "EQUITY", "TSE", "بانک", "IRR"),
    ("شپنا", "پالایش نفت اصفهان", "EQUITY", "TSE", "پالایشگاه", "IRR"),
    ("فارس", "صنایع پتروشیمی خلیج فارس", "EQUITY", "TSE", "پتروشیمی", "IRR"),
    ("ونوک", "ونوک", "EQUITY", "OTC", "فناوری", "IRR"),
    ("BTC", "Bitcoin", "CRYPTO", "BINANCE", "ارز دیجیتال", "USD"),
    ("ETH", "Ethereum", "CRYPTO", "BINANCE", "ارز دیجیتال", "USD"),
]

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"
DEMO_EMAIL = "demo@bedaanwaves.local"


def _hash_password(password: str) -> str:
    import hashlib

    salt = uuid.uuid4().bytes
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256${100000}${salt.hex()}${dk.hex()}"


def _random_walk(start: float, days: int, vol: float, drift: float) -> list[float]:
    import random

    prices: list[float] = []
    price = start
    for _ in range(days):
        shock = random.gauss(drift, vol)
        price = max(price * (1 + shock), 1.0)
        prices.append(price)
    return prices


def _seed_assets(session) -> dict[str, uuid.UUID]:
    ids: dict[str, uuid.UUID] = {}
    for symbol, name, asset_class, market, sector, currency in ASSETS:
        aid = uuid.uuid4()
        ids[symbol] = aid
        session.add(
            Asset(
                id=aid,
                symbol=symbol,
                name=name,
                asset_class=asset_class,
                market=market,
                sector=sector,
                currency=currency,
                active=True,
                listing_date=datetime(2015, 1, 1),
                meta={"seed": True},
            )
        )
    return ids


def _seed_candles(session, asset_ids: dict[str, uuid.UUID]) -> None:
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    starts = {
        "فولاد": 5600, "فملی": 12000, "شستا": 1280, "خودرو": 3100,
        "وبملت": 6500, "شپنا": 4000, "فارس": 9800, "ونوک": 1480,
        "BTC": 64000, "ETH": 3400,
    }
    for symbol, aid in asset_ids.items():
        closes = _random_walk(starts.get(symbol, 1000), 120, 0.018, 0.0008)
        for i, close in enumerate(closes):
            ts = now - timedelta(days=(len(closes) - 1 - i))
            open_p = closes[i - 1] if i > 0 else close * 0.99
            high = max(open_p, close) * (1 + abs(__import__("random").gauss(0, 0.01)))
            low = min(open_p, close) * (1 - abs(__import__("random").gauss(0, 0.01)))
            volume = int(abs(__import__("random").gauss(5_000_000, 2_000_000)) + 500_000)
            session.add(
                PriceCandle(
                    id=uuid.uuid4(),
                    asset_id=aid,
                    timestamp=ts,
                    timeframe="1d",
                    open=Decimal(str(round(open_p, 4))),
                    high=Decimal(str(round(high, 4))),
                    low=Decimal(str(round(low, 4))),
                    close=Decimal(str(round(close, 4))),
                    volume=volume,
                    turnover=Decimal(str(round(close * volume, 2))),
                    transactions=int(volume / 1000),
                    adjusted_close=Decimal(str(round(close, 4))),
                    split_ratio=Decimal("1.0"),
                    source="SEED",
                    data_quality="CONFIRMED",
                )
            )


def _seed_user(session) -> uuid.UUID:
    uid = uuid.uuid4()
    session.add(
        User(
            id=uid,
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            hashed_password=_hash_password(DEMO_PASSWORD),
            full_name="کاربر نمایشی BedaanWaves",
            is_active=True,
            is_admin=False,
            preferred_language="fa",
            theme="light",
            notifications_enabled=True,
        )
    )
    return uid


def _seed_portfolio(session, user_id: uuid.UUID, asset_ids: dict[str, uuid.UUID]) -> None:
    pid = uuid.uuid4()
    session.add(
        Portfolio(
            id=pid,
            user_id=user_id,
            name="پورتفولیو نمایشی",
            description="پورتفولیو ایجاد شده توسط seed",
            portfolio_type="PERSONAL",
            base_currency="IRR",
            target_allocation={"فولاد": 30, "فملی": 25, "شپنا": 20, "ونوک": 25},
            is_public=False,
        )
    )
    holdings = [
        ("فولاد", 5000, 5400),
        ("فملی", 2000, 11800),
        ("شپنا", 3000, 3950),
        ("ونوک", 1500, 1450),
    ]
    for symbol, qty, entry in holdings:
        aid = asset_ids[symbol]
        session.add(
            Position(
                id=uuid.uuid4(),
                portfolio_id=pid,
                asset_id=aid,
                quantity=Decimal(str(qty)),
                entry_price=Decimal(str(entry)),
                entry_date=datetime.now(timezone.utc) - timedelta(days=30),
                current_price=Decimal(str(entry * 1.05)),
                current_value=Decimal(str(qty * entry * 1.05)),
                unrealized_pnl=Decimal(str(qty * entry * 0.05)),
                unrealized_pnl_pct=Decimal("5.0"),
                stop_loss=Decimal(str(entry * 0.93)),
                take_profit=Decimal(str(entry * 1.15)),
                tags=["seed"],
            )
        )


def _seed_signals(session, asset_ids: dict[str, uuid.UUID]) -> None:
    signals = [
        ("فولاد", "BUY", 87.4, "ScoringService-6D"),
        ("فملی", "HOLD", 62.1, "MomentumService"),
        ("خودرو", "SELL", 78.9, "RiskAnalysisService"),
        ("BTC", "BUY", 71.5, "CryptoAnalysisService"),
        ("شپنا", "BUY", 69.2, "FundamentalAnalysisService"),
    ]
    valid_until = datetime.now(timezone.utc) + timedelta(days=1)
    for symbol, stype, conf, model in signals:
        session.add(
            MLSignal(
                id=uuid.uuid4(),
                asset_id=asset_ids[symbol],
                signal_type=stype,
                confidence=Decimal(str(conf)),
                expected_return=Decimal("3.4"),
                expected_volatility=Decimal("2.1"),
                risk_score=Decimal(str(round(100 - conf, 2))),
                reasoning="سیگنال تولید شده توسط داده‌ی نمایشی (seed).",
                technical_factors={"rsi": 54, "macd": "positive"},
                fundamental_factors={"pe": 7.2},
                sentiment_factors={"score": 0.4},
                ml_model_version="v0.1-seed",
                model_name=model,
                model_confidence=Decimal(str(conf)),
                valid_until=valid_until,
                is_active=True,
                win_rate=Decimal("61.0"),
            )
        )


def _seed_alerts(session, user_id: uuid.UUID, asset_ids: dict[str, uuid.UUID]) -> None:
    alerts = [
        ("فولاد", "PRICE", "ABOVE", 6000),
        ("BTC", "SIGNAL", "ABOVE", 70000),
    ]
    for symbol, atype, direction, threshold in alerts:
        session.add(
            Alert(
                id=uuid.uuid4(),
                user_id=user_id,
                asset_id=asset_ids[symbol],
                alert_type=atype,
                condition={"field": "price", "direction": direction},
                threshold_value=Decimal(str(threshold)),
                threshold_direction=direction,
                notification_channel="WEBHOOK",
                is_active=True,
            )
        )


def _clear(session) -> None:
    # حذف از جدول‌های فرزند به والد (رعایت کلیدهای خارجی)
    for model in (Alert, Position, MLSignal, PriceCandle, Portfolio, APILog, User, Asset):
        session.execute(delete(model))


def main() -> None:
    engine = create_engine(SEED_URL, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with Session() as session:
        print("→ پاک‌سازی داده‌های قبلی…")
        _clear(session)
        session.commit()

        print("→ درج assets…")
        asset_ids = _seed_assets(session)
        session.flush()

        print("→ درج price_candles…")
        _seed_candles(session, asset_ids)

        print("→ درج user / portfolio / signals / alerts…")
        user_id = _seed_user(session)
        session.flush()
        _seed_portfolio(session, user_id, asset_ids)
        _seed_signals(session, asset_ids)
        _seed_alerts(session, user_id, asset_ids)

        session.commit()

    with Session() as session:
        counts = {
            "assets": session.query(Asset).count(),
            "price_candles": session.query(PriceCandle).count(),
            "users": session.query(User).count(),
            "portfolios": session.query(Portfolio).count(),
            "positions": session.query(Position).count(),
            "ml_signals": session.query(MLSignal).count(),
            "alerts": session.query(Alert).count(),
        }
    engine.dispose()

    print("\n✅ Seed با موفقیت اجرا شد:")
    for k, v in counts.items():
        print(f"   - {k}: {v}")
    print(f"\n   ورود نمایشی → نام‌کاربری: {DEMO_USERNAME}  |  رمز: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
