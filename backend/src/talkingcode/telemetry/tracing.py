"""Manual OpenInference spans against the Phoenix tracer provider."""

from openinference.instrumentation import OITracer, TraceConfig
from opentelemetry.trace import NoOpTracer, TracerProvider

_tracer: OITracer = OITracer(NoOpTracer(), config=TraceConfig())


def set_phoenix_tracer_provider(provider: TracerProvider) -> None:
    """Route manual OpenInference spans through the Phoenix tracer provider.

    Called once at startup after ``phoenix.otel.register``.  Until then (and
    when Phoenix tracing is disabled) ``get_phoenix_tracer`` hands out a
    no-op tracer, so callers never need to guard span creation.
    """
    global _tracer
    tracer = provider.get_tracer("talkingcode")
    _tracer = (
        tracer if isinstance(tracer, OITracer) else OITracer(tracer, config=TraceConfig())
    )


def get_phoenix_tracer() -> OITracer:
    """Tracer for manual OpenInference spans (``set_input``/``set_output``).

    The OpenAI Agents instrumentor never records input/output on the
    trace-root or agent spans (the SDK's trace and ``AgentSpanData`` carry no
    output field), so surfacing a turn's final output in Phoenix requires a
    manual wrapper span created through this tracer.
    """
    return _tracer
