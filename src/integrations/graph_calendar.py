"""Microsoft Graph (Outlook) calendar integration — app-only, cross-tenant.

Creates study/assessment events (marked Busy) on a sample mailbox in a SEPARATE
Azure AD tenant. Auth is client-credentials, which is issued per-tenant, so pointing
the GRAPH_* env vars at an app registered + admin-consented in the TEST tenant (with
the Calendars.ReadWrite APPLICATION permission) is all that's needed — no link to the
Foundry-hosted tenant.

When the GRAPH_* vars are absent the app never calls Graph; the BFF falls back to a
downloadable .ics built by `build_ics`, so the repo stays runnable with no Azure setup.

Event contract (from api/scheduling.py):
    {"type", "title", "body", "skill", "date", "slot",
     "start_iso": "YYYY-MM-DDTHH:MM:SS", "end_iso": "YYYY-MM-DDTHH:MM:SS"}
"""
from __future__ import annotations
import os

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"

# Configuration function for Graph API settings
def _cfg() -> dict:
    # Read at call time so .env load order never matters.
    return {
        "tenant_id": os.environ.get("GRAPH_TENANT_ID"),
        "client_id": os.environ.get("GRAPH_CLIENT_ID"),
        "client_secret": os.environ.get("GRAPH_CLIENT_SECRET"),
        "default_user": os.environ.get("GRAPH_DEFAULT_USER"),
        "timezone": os.environ.get("GRAPH_TIMEZONE", "UTC"),
    }


def is_configured() -> bool:
    c = _cfg()
    return all(c[k] for k in ("tenant_id", "client_id", "client_secret", "default_user"))


def _token(cfg: dict) -> str:
    """App-only token for the TEST tenant via client credentials."""
    from azure.identity import ClientSecretCredential
    cred = ClientSecretCredential(cfg["tenant_id"], cfg["client_id"], cfg["client_secret"])
    return cred.get_token(GRAPH_SCOPE).token


def _event_payload(ev: dict, timezone: str) -> dict:
    return {
        "subject": ev["title"],
        "body": {"contentType": "HTML", "content": ev.get("body", "")},
        "start": {"dateTime": ev["start_iso"], "timeZone": timezone},
        "end": {"dateTime": ev["end_iso"], "timeZone": timezone},
        "showAs": "busy",                 # blocks the calendar
        "isReminderOn": True,
        "reminderMinutesBeforeStart": 30,
        "categories": ["ASCENT"],
    }


def create_events(events: list[dict], target_user: str | None = None) -> dict:
    """Create each event on the target mailbox's calendar. Resilient per-event."""
    import httpx
    cfg = _cfg()
    target_user = target_user or cfg["default_user"]
    if not is_configured():
        return {"created": 0, "failed": len(events), "errors": ["Graph not configured"],
                "target_user": target_user}
    token = _token(cfg)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    created, failed, errors = 0, 0, []
    url = f"{GRAPH_BASE}/users/{target_user}/events"
    with httpx.Client(timeout=20) as client:
        for ev in events:
            try:
                resp = client.post(url, headers=headers, json=_event_payload(ev, cfg["timezone"]))
                if resp.status_code in (200, 201):
                    created += 1
                else:
                    failed += 1
                    errors.append(f"{ev.get('title','event')}: {resp.status_code} {resp.text[:160]}")
            except Exception as exc:  # network/auth — keep going, report
                failed += 1
                errors.append(f"{ev.get('title','event')}: {type(exc).__name__}: {exc}")
    return {"created": created, "failed": failed, "errors": errors[:5], "target_user": target_user}


# ── .ics fallback (no Graph / no tenant required) ─────────────────────────────

def _ics_dt(iso: str) -> str:
    """'2026-06-16T09:00:00' -> '20260616T090000' (floating local time)."""
    return iso.replace("-", "").replace(":", "")


def _ics_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def build_ics(events: list[dict]) -> str:
    """Minimal valid iCalendar for the events (TRANSP:OPAQUE = Busy)."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ASCENT//Study Plan//EN", "CALSCALE:GREGORIAN"]
    for i, ev in enumerate(events):
        lines += [
            "BEGIN:VEVENT",
            f"UID:ascent-{i}-{_ics_dt(ev.get('start_iso',''))}@ascent.demo",
            f"DTSTART:{_ics_dt(ev['start_iso'])}",
            f"DTEND:{_ics_dt(ev['end_iso'])}",
            f"SUMMARY:{_ics_escape(ev.get('title',''))}",
            f"DESCRIPTION:{_ics_escape(ev.get('body',''))}",
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
