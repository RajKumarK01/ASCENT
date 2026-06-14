"""Foundry Hosted Agent entrypoint (Responses protocol).

The container is deployed to Foundry Agent Service as a hosted agent
(`kind: hosted`). Foundry pulls the image, provisions a per-session sandbox,
assigns a Microsoft Entra agent identity, and exposes the Responses endpoint at
{project}/agents/<name>/endpoint/protocols/openai/responses.

The agent's *custom code* (the ASCENT orchestrator + five specialists + IQ
layers) handles orchestration; it calls Foundry models for reasoning. The
Responses server library handles the HTTP server, health checks, streaming,
cancellation, and OpenTelemetry wiring on port 8088 ($PORT).

Set ASCENT_SERVER=local to run the tiny dev HTTP loop instead (curl-able
without the agentserver library) — useful before deploying.

Telemetry: when APPLICATIONINSIGHTS_CONNECTION_STRING is set (auto-injected by
the Foundry runtime), OpenTelemetry traces are emitted so the agent flow is
visible in Application Insights Transaction Search.
"""
from __future__ import annotations
import asyncio
import json
import os
import re

from .orchestrator import run_for_learner
from .config import MODE, MODEL_DEPLOYMENT

PORT = int(os.environ.get("PORT", "8088"))
_LEARNER_RE = re.compile(r"L-\d{4}")
_MAX_INPUT_LEN = 4096

# Foundry agent registration is a one-time setup step, not a per-boot action.
# See scripts/register_foundry_agents.py (prompt specialists) and
# scripts/deploy_hosted_agent.py (this hosted orchestrator).


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


def _render(result: dict) -> str:
    """Render the orchestrator result dict into a readable answer for the playground.

    Keeps the full reasoning trace so the multi-agent flow is visible, and appends
    the raw structured payload for programmatic consumers.
    """
    if result.get("error"):
        return f"{result['error']}\n\n_{result.get('disclaimer', '')}_"

    cur = result.get("curator", {}) or {}
    plan = result.get("study_plan", {}) or {}
    asmt = result.get("assessment", {}) or {}
    readiness = asmt.get("readiness", {}) or {}
    video = result.get("recommended_video") or {}

    lines: list[str] = []
    lines.append(f"# Learning plan for {result.get('learner_id', '?')} "
                 f"({cur.get('role', '?')} → {cur.get('certification', '?')})")
    lines.append("")
    lines.append(f"**Agent route:** {' → '.join(result.get('route', []))}")
    lines.append("")

    if cur.get("content_summary"):
        lines.append("## Curated path")
        lines.append(cur["content_summary"])
        lines.append("")

    lines.append("## Study plan")
    lines.append(f"- {plan.get('total_recommended_hours', '?')}h over "
                 f"{plan.get('weeks', '?')} weeks "
                 f"({plan.get('hours_per_week', '?')}h/week)")
    milestones = plan.get("milestones", []) or []
    if milestones:
        lines.append(f"- {len(milestones)} milestones")
    lines.append("")

    verdict = "READY ✅" if result.get("passed") else "NOT READY — continue preparation"
    lines.append("## Readiness")
    lines.append(f"- **{verdict}**")
    if readiness:
        lines.append(f"- score gap: {readiness.get('score_gap', 'n/a')}, "
                     f"hours gap: {readiness.get('hours_gap', 'n/a')}h")
    if result.get("next_step"):
        lines.append(f"- Next step: {result['next_step']}")
    lines.append(f"- Self-reflection loops: {result.get('loops', 0)}")
    lines.append("")

    citations = cur.get("citations", []) or []
    if citations:
        lines.append("## Citations")
        for c in citations:
            lines.append(f"- {c}")
        lines.append("")

    if video.get("title"):
        lines.append(f"**Recommended video:** {video['title']}")
        lines.append("")

    trace = result.get("trace", []) or []
    if trace:
        lines.append("## Reasoning trace")
        for step in trace:
            lines.append(f"- {step}")
        lines.append("")

    lines.append(f"_{result.get('disclaimer', '')}_")
    if result.get("human_in_the_loop"):
        lines.append(f"_{result['human_in_the_loop']}_")

    return "\n".join(lines)


def _run_responses_server() -> None:
    """Serve the Foundry Responses protocol (production / hosted-agent path)."""
    from azure.ai.agentserver.responses import (
        ResponsesAgentServerHost,
        ResponsesServerOptions,
        TextResponse,
    )

    app = ResponsesAgentServerHost(
        options=ResponsesServerOptions(default_model=MODEL_DEPLOYMENT)
    )

    @app.response_handler
    async def _handler(request, context, cancellation_signal):  # noqa: ANN001
        text = await context.get_input_text()
        # run_for_learner is synchronous (uses a thread pool internally); offload
        # it so the event loop stays responsive to cancellation/health checks.
        result = await asyncio.to_thread(handle, text)
        return TextResponse(context, request, text=_render(result))

    print(f"ASCENT Responses server starting on 0.0.0.0:{PORT}")
    app.run()  # binds $PORT or 8088


def _run_local_http() -> None:
    """Tiny dev HTTP loop — curl-able without the agentserver library."""
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

    print(f"ASCENT local dev server on http://localhost:{PORT}/responses")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    _configure_telemetry()
    if os.environ.get("ASCENT_SERVER", "responses").lower() == "local":
        _run_local_http()
    else:
        _run_responses_server()
