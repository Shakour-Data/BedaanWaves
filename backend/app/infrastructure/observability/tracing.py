import logging
from typing import Any

from app.core.utils import utc_now_iso

logger = logging.getLogger(__name__)


def _setup_otlp_exporter(provider, endpoint: str | None = None) -> None:
    """Attach an OTLP span exporter to the given TracerProvider."""
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    kwargs: dict[str, Any] = {}
    if endpoint:
        kwargs["endpoint"] = endpoint
    processor = BatchSpanProcessor(OTLPSpanExporter(**kwargs))
    provider.add_span_processor(processor)


def _setup_jaeger_exporter(provider, endpoint: str | None = None) -> None:
    """Attach a Jaeger Thrift exporter as a fallback."""
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter

        processor = BatchSpanProcessor(
            JaegerExporter(endpoint=endpoint, insecure=True)
        )
        provider.add_span_processor(processor)
    except ImportError:
        logger.warning("Jaeger exporter package not installed; skipping jaeger exporter")


class TracingManager:
    def __init__(
        self,
        service_name: str = "bedaanwaves",
        enabled: bool = True,
        otlp_endpoint: str | None = None,
        jaeger_endpoint: str | None = None,
        use_otlp: bool = True,
    ):
        self.service_name = service_name
        self.enabled = enabled
        self._tracer = None
        self._otlp_endpoint = otlp_endpoint
        self._jaeger_endpoint = jaeger_endpoint
        self._use_otlp = use_otlp

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
                {"service.name": self.service_name, "service.start_time": utc_now_iso()}
            )
            provider = TracerProvider(resource=resource)

            if self._use_otlp or self._otlp_endpoint:
                _setup_otlp_exporter(provider, endpoint=self._otlp_endpoint)
            elif self._jaeger_endpoint:
                _setup_jaeger_exporter(provider, endpoint=self._jaeger_endpoint)

            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(self.service_name)
            logger.info("OpenTelemetry tracing initialized")
        except ImportError:
            logger.warning("OpenTelemetry packages not installed; tracing disabled")
        except Exception as exc:
            logger.warning("Tracing initialization failed: %s", exc)

    def instrument_app(self, app: Any) -> None:
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

    def get_tracer(self, name: str):
        if not self.enabled:
            return None
        try:
            from opentelemetry import trace

            return trace.get_tracer(name)
        except Exception:
            return None
