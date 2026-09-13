"""
Tracing Manager - OpenTelemetry tracing with Jaeger export.

Supports both OTLP gRPC (port 4317) and Jaeger Thrift HTTP (port 14268)
exporters.  Auto-instruments FastAPI, SQLAlchemy, and Redis so that
end-to-end traces are available without manual span creation.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TracingManager:
    """Manages OpenTelemetry tracing lifecycle."""

    def __init__(
        self,
        service_name: str = "bedaanwaves",
        enabled: bool = True,
        otlp_endpoint: str | None = None,
        jaeger_endpoint: str | None = None,
        use_otlp: bool = False,
    ):
        self.service_name = service_name
        self.enabled = enabled
        self.otlp_endpoint = otlp_endpoint or "http://localhost:4317"
        self.jaeger_endpoint = jaeger_endpoint or "http://localhost:14268/api/traces"
        self.use_otlp = use_otlp
        self._tracer = None

    async def initialize(self) -> None:
        if not self.enabled:
            logger.info("Tracing disabled by configuration")
            return

        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource.create(
                {
                    "service.name": self.service_name,
                    "service.version": "1.0.0",
                    "telemetry.sdk.language": "python",
                    "telemetry.sdk.name": "opentelemetry",
                }
            )

            provider = TracerProvider(resource=resource)

            if self.use_otlp:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint, insecure=True)
                logger.info("Using OTLP gRPC exporter → %s", self.otlp_endpoint)
            else:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                exporter = JaegerExporter(
                    endpoint=self.jaeger_endpoint,
                )
                logger.info("Using Jaeger Thrift HTTP exporter → %s", self.jaeger_endpoint)

            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(self.service_name)
            logger.info("OpenTelemetry tracing initialized (service=%s)", self.service_name)

        except ImportError:
            logger.warning("OpenTelemetry packages not installed; tracing disabled")
        except Exception as exc:
            logger.warning("Tracing initialization failed: %s", exc)

    def instrument_app(self, app: Any) -> None:
        """Auto-instrument a FastAPI application."""
        if not self.enabled or self._tracer is None:
            return
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented for tracing")
        except ImportError:
            logger.warning("FastAPI instrumentation package not installed")
        except Exception as exc:
            logger.warning("FastAPI instrumentation failed: %s", exc)

    def instrument_database(self, engine: Any) -> None:
        """Auto-instrument a SQLAlchemy engine."""
        if not self.enabled or self._tracer is None:
            return
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumented for tracing")
        except ImportError:
            logger.warning("SQLAlchemy instrumentation package not installed")
        except Exception as exc:
            logger.warning("SQLAlchemy instrumentation failed: %s", exc)

    def instrument_redis(self, redis_client: Any) -> None:
        """Auto-instrument a Redis client."""
        if not self.enabled or self._tracer is None:
            return
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor

            RedisInstrumentor().instrument(redis_client)
            logger.info("Redis instrumented for tracing")
        except ImportError:
            logger.warning("Redis instrumentation package not installed")
        except Exception as exc:
            logger.warning("Redis instrumentation failed: %s", exc)

    def get_tracer(self, name: str):
        if not self.enabled:
            return None
        try:
            from opentelemetry import trace
            return trace.get_tracer(name)
        except Exception:
            return None
