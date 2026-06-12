"""Hosted Agent entrypoint (Foundry Responses protocol).

LOCAL: runs a tiny HTTP loop so you can curl the agent before deploying.
FOUNDRY: replace the handler body with the `azure-ai-agentserver-responses`
IResponseHandler implementation. The container serves /responses on :8088.
See BUILD_STEPS/08 and Microsoft Learn MCP: "Deploy a hosted agent".

Telemetry: when APPLICATIONINSIGHTS_CONNECTION_STRING is set (auto-injected by
Foundry Hosted Agent runtime), OpenTelemetry traces are emitted so the agent-to-
agent flow is visible in Application Insights Transaction Search.
"""
from __future__ import annotations
import json
import os
import re

from .orchestrator import run_for_learner
from .config import MODE

PORT = int(os.environ.get("PORT", "8088"))
_LEARNER_RE = re.compile(r"L-\d{4}")
_MAX_INPUT_LEN = 4096


def _configure_telemetry() -> None:
    """Wire OpenTelemetry -> Application Insights when the connection string is present."""
    conn_str = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn_str:
        return
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor(connection_string=conn_str)
    except ImportError:
        pass  # azure-monitor-opentelemetry not installed; skip silently


def handle(message: str) -> dict:
    """Map a free-text request to the orchestrator. Extract a synthetic learner id."""
    if len(message or "") > _MAX_INPUT_LEN:
        return {
            "error": f"Input too long (max {_MAX_INPUT_LEN} characters).",
            "disclaimer": "You are interacting with an AI system. Synthetic demo data only.",
        }
    m = _LEARNER_RE.search(message or "")
    learner_id = m.group(0) if m else "L-1001"

    if MODE == "foundry":
        from opentelemetry import trace
        tracer = trace.get_tracer("ascent.orchestrator")
        with tracer.start_as_current_span("orchestrator.run") as span:
            span.set_attribute("learner_id", learner_id)
            result = run_for_learner(learner_id)
            span.set_attribute("passed", result.get("passed", False))
            span.set_attribute("loops", result.get("loops", 0))
    else:
        result = run_for_learner(learner_id)

    return result


def _run_local_http() -> None:
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            result = handle(body.get("input") or body.get("message", ""))
            payload = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_):  # quiet
            pass

    print(f"ASCENT local server on http://localhost:{PORT}/responses")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    _configure_telemetry()
    # TODO(step-08): swap to azure-ai-agentserver-responses IResponseHandler.
    _run_local_http()
