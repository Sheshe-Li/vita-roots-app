"""
Phoenix Arize observability setup with OpenInference Anthropic instrumentation.
This module MUST be imported and initialized before any Anthropic client is created.
"""

import os
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from openinference.instrumentation.anthropic import AnthropicInstrumentor
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

_tracer_provider: Optional[TracerProvider] = None
_instrumentor: Optional[AnthropicInstrumentor] = None
_phoenix_initialized: bool = False


def init_observability() -> bool:
    """
    Initialize Phoenix Arize observability with OpenTelemetry.
    Must be called before any Anthropic client is instantiated.
    Returns True if Phoenix connection succeeded, False otherwise.
    """
    global _tracer_provider, _instrumentor, _phoenix_initialized

    phoenix_endpoint = os.getenv(
        "PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces"
    )
    project_name = os.getenv("PHOENIX_PROJECT_NAME", "vita-roots-app")
    phoenix_api_key = os.getenv("PHOENIX_API_KEY", "")

    resource = Resource(
        attributes={
            ResourceAttributes.SERVICE_NAME: project_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
            "project.name": project_name,
        }
    )

    _tracer_provider = TracerProvider(resource=resource)

    # Build OTLP headers — include API key when using Phoenix Cloud
    otlp_headers: dict[str, str] = {}
    if phoenix_api_key:
        otlp_headers["Authorization"] = f"Bearer {phoenix_api_key}"
        logger.info("Phoenix Cloud API key loaded — sending authenticated traces.")
    else:
        logger.info("No PHOENIX_API_KEY set — connecting to local Phoenix instance.")

    # Primary exporter: Phoenix via OTLP HTTP
    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=phoenix_endpoint,
            headers=otlp_headers,
        )
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        _phoenix_initialized = True
        logger.info(f"Phoenix OTLP exporter configured: {phoenix_endpoint}")
    except Exception as exc:
        logger.warning(f"Failed to configure Phoenix exporter: {exc}. Falling back to console.")
        _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        _phoenix_initialized = False

    # Register as global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Instrument Anthropic SDK — wraps every API call automatically
    _instrumentor = AnthropicInstrumentor()
    _instrumentor.instrument(tracer_provider=_tracer_provider)
    logger.info("AnthropicInstrumentor active — all Anthropic calls will be traced.")

    return _phoenix_initialized


def get_tracer(name: str = "vita-roots-app") -> trace.Tracer:
    """Return an OpenTelemetry tracer for manual span creation."""
    return trace.get_tracer(name)


def add_wellness_attributes(
    span: trace.Span,
    *,
    family_id: Optional[str] = None,
    member_id: Optional[str] = None,
    request_type: Optional[str] = None,
    model: Optional[str] = None,
) -> None:
    """
    Attach family-wellness-specific attributes to a span.

    Args:
        span: Active OpenTelemetry span.
        family_id: UUID of the family.
        member_id: UUID of the family member.
        request_type: One of meal_plan | grocery | supplement | chat.
        model: Anthropic model identifier used for the request.
    """
    if family_id:
        span.set_attribute("family.id", family_id)
    if member_id:
        span.set_attribute("family.member_id", member_id)
    if request_type:
        span.set_attribute("wellness.request_type", request_type)
    if model:
        span.set_attribute("llm.model", model)


def is_phoenix_connected() -> bool:
    """Return whether Phoenix was successfully initialized."""
    return _phoenix_initialized


def shutdown_observability() -> None:
    """Flush and shut down the tracer provider gracefully."""
    if _tracer_provider:
        _tracer_provider.shutdown()
        logger.info("Tracer provider shut down.")
