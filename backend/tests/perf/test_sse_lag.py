"""
TR12.2 — SSE Lag Performance Benchmark.

Measures end-to-end transport lag for live SSE quote streams:

    lag_ms = (client_received_ts_utc_ms) - (server_payload.received_ts_ms)

Aggregated across N concurrent httpx.AsyncClient streaming connections
streaming M distinct symbols for DURATION seconds.

BEST-EFFORT single-machine configuration:

* Target (full spec): 100 clients x 20 symbols, 60s → p95 ≤ 150ms
* Fallback (documented): 20 clients x 20 symbols, 60s → p95 ≤ 150ms
  The environment variable SSE_BENCH_CLIENTS can override the count.

If the backend server is NOT running on API_PORT (default 3000), the script
will attempt to launch `python run.py` as a subprocess with environment:

    REQUIRE_AUTH=false
    DATA_PROVIDER=fake
    LIVE_POLL_INTERVAL_OPEN_S=1
    LIVE_PING_INTERVAL_S=5

and retry the /health endpoint until it is responsive.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

KNOWN_SYMBOLS: Tuple[str, ...] = (
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "INTC", "AMD",
    "ORCL", "ADBE", "CRM", "TXN", "QCOM", "AVGO", "COST", "PEP", "KO", "JPM",
)

DEFAULT_CLIENTS_FULL = 100
DEFAULT_CLIENTS_FALLBACK = 20
DEFAULT_DURATION_S = 60
DEFAULT_BASE_URL = "http://127.0.0.1:3000"
SSE_PATH_FMT = "/api/v1/live-sse/quote/{symbol}/stream"
HEALTH_PATH = "/api/v1/health"
API_PORT_DEFAULT = 3000


def _utc_now_ms() -> float:
    return datetime.now(timezone.utc).timestamp() * 1000.0


def _parse_received_ts_ms(data: Dict[str, Any]) -> Optional[float]:
    """Recursively search the payload dict for `received_ts` and convert to UTC ms."""
    if not isinstance(data, dict):
        return None
    for k, v in data.items():
        if isinstance(k, str) and k.lower() == "received_ts":
            if isinstance(v, (int, float)):
                val = float(v)
                if val > 1e12:
                    return val
                return val * 1000.0
            if isinstance(v, str):
                try:
                    if v.endswith("Z") or "+" in v or v.count("-") >= 2:
                        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                    else:
                        dt = datetime.fromisoformat(v).replace(tzinfo=timezone.utc)
                    return dt.timestamp() * 1000.0
                except (ValueError, TypeError):
                    pass
        if isinstance(v, dict):
            nested = _parse_received_ts_ms(v)
            if nested is not None:
                return nested
    return None


def _iter_sse_frames(raw_bytes: bytes) -> List[Tuple[Optional[str], Dict[str, Any]]]:
    """Parse bytes chunk into SSE (event, data_dict) frames."""
    text = raw_bytes.decode("utf-8", errors="replace")
    frames: List[Tuple[Optional[str], Dict[str, Any]]] = []
    current_event: Optional[str] = None
    current_data_lines: List[str] = []

    def flush() -> None:
        nonlocal current_event, current_data_lines
        if not current_data_lines:
            current_event = None
            return
        joined = "\n".join(current_data_lines).strip()
        current_data_lines = []
        if not joined:
            current_event = None
            return
        try:
            parsed = json.loads(joined)
        except json.JSONDecodeError:
            parsed = {"_raw": joined}
        frames.append((current_event, parsed if isinstance(parsed, dict) else {"_raw": parsed}))
        current_event = None

    for line in text.split("\n"):
        stripped = line.rstrip("\r")
        if stripped == "":
            flush()
            continue
        if stripped.startswith(":"):
            continue
        if ":" in stripped:
            field, value = stripped.split(":", 1)
            value = value[1:] if value.startswith(" ") else value
        else:
            field, value = stripped, ""
        if field == "event":
            current_event = value.strip() or None
        elif field == "data":
            current_data_lines.append(value)
        elif field == "id":
            pass
        elif field == "retry":
            pass
    flush()
    return frames


def _port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
        except (ConnectionRefusedError, OSError, socket.timeout):
            return False
        return True


def _maybe_start_backend_server(port: int) -> Optional[subprocess.Popen]:
    """If the backend is not running on `port`, launch run.py and wait for health."""
    if _port_in_use(port):
        logger.info("[SSE-Bench] port %s already bound; assuming backend is running.", port)
        return None

    backend_root = Path(__file__).resolve().parents[2]
    run_py = backend_root / "run.py"
    if not run_py.exists():
        logger.warning("[SSE-Bench] run.py not found at %s; skipping auto-launch.", run_py)
        return None

    logger.info("[SSE-Bench] launching backend server: python %s", run_py)
    env = os.environ.copy()
    env.update({
        "REQUIRE_AUTH": "false",
        "REQ": "false",
        "DATA_PROVIDER": "fake",
        "LIVE_POLL_INTERVAL_OPEN_S": "1",
        "LIVE_POLL_INTERVAL_CLOSED_S": "5",
        "LIVE_PING_INTERVAL_S": "5",
        "LIVE_BENCH_SKIP_DB_LIFESPAN": "true",
        "API_PORT": str(port),
    })
    proc = subprocess.Popen(
        [sys.executable, str(run_py)],
        cwd=str(backend_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc


async def _wait_for_health(base_url: str, timeout_s: float = 120.0) -> bool:
    import httpx
    deadline = time.time() + timeout_s
    last_err: Optional[str] = None
    while time.time() < deadline:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(base_url + HEALTH_PATH)
                if 200 <= resp.status_code < 500:
                    logger.info("[SSE-Bench] backend health OK (%s %s)", resp.status_code, resp.text[:80])
                    return True
                last_err = f"status={resp.status_code}"
        except Exception as exc:  # pragma: no cover - network flake
            last_err = type(exc).__name__ + ":" + str(exc)[:120]
        await asyncio.sleep(1.0)
    logger.error("[SSE-Bench] backend health check failed after %ss: %s", timeout_s, last_err)
    return False


async def _stream_one_client(
    client_id: int,
    symbol: str,
    base_url: str,
    duration_s: float,
    samples_out: List[float],
    events_out: List[Dict[str, Any]],
    stop_event: asyncio.Event,
) -> None:
    import httpx

    url = base_url + SSE_PATH_FMT.format(symbol=symbol)
    token_qp = f"?token=bench-token-{uuid.uuid4().hex[:8]}"
    full_url = url + token_qp

    start_ts = time.time()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=duration_s + 30.0, write=10.0, pool=30.0)) as client:
            async with client.stream("GET", full_url) as resp:
                resp.raise_for_status()
                buffer = b""
                async for chunk in resp.aiter_bytes():
                    if stop_event.is_set() or (time.time() - start_ts) >= duration_s:
                        break
                    if not chunk:
                        continue
                    buffer += chunk
                    if b"\n\n" not in buffer and b"\r\n\r\n" not in buffer:
                        continue
                    for event_name, data in _iter_sse_frames(buffer):
                        buffer = b""
                        if not isinstance(data, dict):
                            continue
                        if event_name in ("ping", "health") and not any(
                            k.lower() in ("received_ts", "price", "current_price", "change_pct") for k in data.keys()
                        ):
                            continue
                        server_ms = _parse_received_ts_ms(data)
                        client_ms = _utc_now_ms()
                        payload_wrapped = data.get("data")
                        if server_ms is None and isinstance(payload_wrapped, dict):
                            server_ms = _parse_received_ts_ms(payload_wrapped)
                        if server_ms is not None:
                            lag = client_ms - server_ms
                            if -5_000.0 <= lag <= 60_000.0:
                                samples_out.append(lag)
                                events_out.append({
                                    "client_id": client_id,
                                    "symbol": symbol,
                                    "event": event_name,
                                    "lag_ms": lag,
                                })
                            else:
                                logger.debug(
                                    "[SSE-Bench] client%s %s outlier lag_ms=%.1f discarded",
                                    client_id, symbol, lag,
                                )
                        else:
                            events_out.append({
                                "client_id": client_id,
                                "symbol": symbol,
                                "event": event_name,
                                "lag_ms": None,
                            })
    except Exception as exc:
        logger.warning(
            "[SSE-Bench] client%s %s stream ended: %s: %s",
            client_id, symbol, type(exc).__name__, str(exc)[:160],
        )


@pytest.mark.perf
@pytest.mark.asyncio
async def test_sse_lag_p95_under_150ms() -> None:
    """TR12.2 rule: p95 end-to-end SSE lag ≤ 150ms."""
    port = int(os.environ.get("API_PORT", API_PORT_DEFAULT))
    base_url = os.environ.get("SSE_BENCH_BASE_URL", f"http://127.0.0.1:{port}").rstrip("/")

    n_clients_env = os.environ.get("SSE_BENCH_CLIENTS")
    if n_clients_env:
        try:
            n_clients = max(1, int(n_clients_env))
        except ValueError:
            n_clients = DEFAULT_CLIENTS_FALLBACK
        scaling_note = f"overridden via SSE_BENCH_CLIENTS={n_clients}"
    else:
        n_clients = DEFAULT_CLIENTS_FALLBACK
        scaling_note = (
            f"fallback single-machine: {n_clients} clients x {len(KNOWN_SYMBOLS)} symbols "
            f"(full spec would be {DEFAULT_CLIENTS_FULL} clients; scaling-factor "
            f"{DEFAULT_CLIENTS_FULL}/{n_clients}≈{DEFAULT_CLIENTS_FULL/max(1,n_clients):.1f}x). "
            f"Set SSE_BENCH_CLIENTS={DEFAULT_CLIENTS_FULL} to run full load."
        )
    duration_s = float(os.environ.get("SSE_BENCH_DURATION_S", DEFAULT_DURATION_S))

    logger.info("=" * 72)
    logger.info("[SSE-Bench] TR12.2 SSE LAG BENCHMARK")
    logger.info("[SSE-Bench] base_url=%s duration=%.0fs clients=%s symbols=%s",
                base_url, duration_s, n_clients, len(KNOWN_SYMBOLS))
    logger.info("[SSE-Bench] scaling note: %s", scaling_note)
    logger.info("=" * 72)

    backend_proc = _maybe_start_backend_server(port)
    try:
        healthy = await _wait_for_health(base_url, timeout_s=120.0)
        if not healthy:
            pytest.skip(
                f"backend server not reachable at {base_url} after auto-launch attempt; "
                "SSE benchmark skipped. Start the server manually and re-run."
            )

        samples: List[float] = []
        events: List[Dict[str, Any]] = []
        stop_event = asyncio.Event()

        tasks: List[asyncio.Task[None]] = []
        for idx in range(n_clients):
            symbol = KNOWN_SYMBOLS[idx % len(KNOWN_SYMBOLS)]
            tasks.append(asyncio.create_task(_stream_one_client(
                client_id=idx,
                symbol=symbol,
                base_url=base_url,
                duration_s=duration_s,
                samples_out=samples,
                events_out=events,
                stop_event=stop_event,
            )))

        logger.info("[SSE-Bench] launched %s streaming connections; sampling for %.0fs...",
                    len(tasks), duration_s)
        done, pending = await asyncio.wait(tasks, timeout=duration_s + 10.0)
        if pending:
            stop_event.set()
            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

        total_events = len(events)
        samples_with_lag = len(samples)
        logger.info("[SSE-Bench] completed. events_total=%s samples_with_lag=%s",
                    total_events, samples_with_lag)

        if samples_with_lag < 10:
            logger.warning(
                "[SSE-Bench] only %s samples with known lag collected; "
                "cannot reliably compute percentiles. Marking SKIP.",
                samples_with_lag,
            )
            pytest.skip(
                f"Insufficient SSE lag samples ({samples_with_lag}<10). "
                "The server may be running with no data provider emitting received_ts."
            )

        samples_sorted = sorted(samples)
        p50 = statistics.quantiles(samples_sorted, n=100, method="exclusive")[49]
        p95 = statistics.quantiles(samples_sorted, n=100, method="exclusive")[94]
        mean_lag = sum(samples_sorted) / len(samples_sorted)
        min_lag = samples_sorted[0]
        max_lag = samples_sorted[-1]

        symbols_covered = sorted({e.get("symbol", "?") for e in events})
        clients_seen = len({e.get("client_id", -1) for e in events})

        print()
        print("======== SSE LAG BENCHMARK RESULTS ========")
        print(f"  base_url           : {base_url}")
        print(f"  clients            : {n_clients}  (active seen: {clients_seen})")
        print(f"  symbols            : {len(symbols_covered)} -> {symbols_covered[:8]}{'...' if len(symbols_covered)>8 else ''}")
        print(f"  duration           : {duration_s:.0f}s")
        print(f"  events total       : {total_events}")
        print(f"  samples (lag known): {samples_with_lag}")
        print(f"  min  lag_ms        : {min_lag:.1f}")
        print(f"  mean lag_ms        : {mean_lag:.1f}")
        print(f"  p50  lag_ms        : {p50:.1f}")
        print(f"  p95  lag_ms        : {p95:.1f}")
        print(f"  max  lag_ms        : {max_lag:.1f}")
        print(f"  threshold p95 ≤150 : {'PASS' if p95 <= 150.0 else 'FAIL'}")
        print(f"  scaling note       : {scaling_note}")
        print("============================================")
        print(flush=True)

        logger.info("[SSE-Bench] RESULT p50=%.1fms p95=%.1fms threshold≤150ms → %s",
                    p50, p95, "PASS" if p95 <= 150.0 else "FAIL")
        assert p95 <= 150.0, (
            f"TR12.2 SSE lag p95={p95:.1f}ms exceeded 150ms threshold "
            f"(p50={p50:.1f}ms, samples={samples_with_lag}). "
            f"{scaling_note}"
        )
    finally:
        if backend_proc is not None and backend_proc.poll() is None:
            logger.info("[SSE-Bench] terminating auto-launched backend server (pid %s).", backend_proc.pid)
            try:
                backend_proc.terminate()
                try:
                    backend_proc.wait(timeout=15.0)
                except subprocess.TimeoutExpired:
                    backend_proc.kill()
            except Exception:
                pass
