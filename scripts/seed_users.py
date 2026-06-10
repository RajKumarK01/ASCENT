"""Generate data/demo_users.json with bcrypt-hashed passwords.

Run once:  python scripts/seed_users.py
All credentials are synthetic and non-secret — safe to document in README.
"""
import json, bcrypt
from pathlib import Path

USERS = [
    {"email": "emp.morgan@ascent.demo", "password": "demo-pass-1", "role": "employee", "scope": "L-1001", "name": "Morgan"},
    {"email": "emp.alex@ascent.demo",   "password": "demo-pass-2", "role": "employee", "scope": "L-1002", "name": "Alex"},
    {"email": "emp.casey@ascent.demo",  "password": "demo-pass-3", "role": "employee", "scope": "L-1004", "name": "Casey"},
    {"email": "mgr.taylor@ascent.demo", "password": "demo-mgr",    "role": "manager",  "scope": "TEAM-A",    "name": "Taylor"},
    {"email": "mgr.jordan@ascent.demo", "password": "demo-mgr2",   "role": "manager",  "scope": "all_teams", "name": "Jordan"},
]

out = []
for u in USERS:
    pw_hash = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt()).decode()
    out.append({"email": u["email"], "name": u["name"],
                "password_hash": pw_hash, "role": u["role"], "scope": u["scope"]})

dest = Path(__file__).parent.parent / "data" / "demo_users.json"
dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(f"Wrote {len(out)} users to {dest}")
for u in USERS:
    print(f"  {u['email']:35s}  pw={u['password']:12s}  role={u['role']:8s}  scope={u['scope']}")
