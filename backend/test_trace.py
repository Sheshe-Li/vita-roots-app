"""
Send a test trace to Phoenix Arize and confirm it was exported.
Run: python test_trace.py
"""

import time
from dotenv import load_dotenv

load_dotenv()

# Must init observability before any Anthropic client is created
from observability import init_observability, get_tracer

print("Initialising Phoenix connection...")
connected = init_observability()
print(f"Phoenix initialized: {connected}\n")

tracer = get_tracer("vita-roots-test")

with tracer.start_as_current_span("test.env_check") as root:
    root.set_attribute("test.source", "test_trace.py")
    root.set_attribute("test.purpose", "env connectivity verification")

    with tracer.start_as_current_span("test.signal_pipeline") as span:
        span.set_attribute("signal.type", "research")
        span.set_attribute("signal.score", 8)
        span.set_attribute("signal.decision", "fire")
        time.sleep(0.05)   # simulate work

    with tracer.start_as_current_span("test.wellness_agent") as span:
        span.set_attribute("family.id", "a1000000-0000-0000-0000-000000000001")
        span.set_attribute("wellness.request_type", "meal_plan")
        span.set_attribute("llm.model", "claude-sonnet-4-6")
        time.sleep(0.05)

print("Trace recorded — flushing to Phoenix Arize...")

# Force flush so BatchSpanProcessor ships spans before process exits
from opentelemetry import trace
provider = trace.get_tracer_provider()
provider.force_flush(timeout_millis=10_000)

print("Done. Open Phoenix Arize → project 'VitaRoots' to see the trace.")
print("Look for span: test.env_check  with children  test.signal_pipeline  and  test.wellness_agent")
