"""Smoke test for the cross-tenant Outlook (Microsoft Graph) calendar integration.

Acquires an app-only token for the TEST tenant (client credentials) and creates ONE
test event on GRAPH_DEFAULT_USER's calendar. Run after filling the GRAPH_* values in
`.env` and granting admin consent for the Calendars.ReadWrite APPLICATION permission
in the test tenant.

    pip install azure-identity httpx python-dotenv
    py scripts/test_graph_calendar.py
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src.integrations import graph_calendar  # noqa: E402

if not graph_calendar.is_configured():
    print("GRAPH_* not configured in .env — nothing to test.")
    print("(The app falls back to a downloadable .ics when these are unset.)")
    sys.exit(1)

start = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
event = {
    "type": "study",
    "skill": "Test",
    "title": "ASCENT smoke-test event",
    "body": "Created by scripts/test_graph_calendar.py — safe to delete.",
    "start_iso": start.strftime("%Y-%m-%dT%H:%M:%S"),
    "end_iso": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
}

print("Creating one test event on the configured mailbox...")
result = graph_calendar.create_events([event])
print(result)
if result["created"]:
    print("OK — check the mailbox's Outlook calendar (event is marked Busy).")
else:
    print("FAILED — see errors above. Common causes: missing admin consent, wrong "
          "GRAPH_DEFAULT_USER UPN, or the app lacks Calendars.ReadWrite (Application).")
