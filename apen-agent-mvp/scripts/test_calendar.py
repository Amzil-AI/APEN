#!/usr/bin/env python3
"""
Test Google Calendar connectivity with credentials from .env.
Run from apen-agent-mvp/: python scripts/test_calendar.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
_env = ROOT / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

sys.path.insert(0, str(ROOT))
from src import calendar_client

def main():
    print("Calendar configuration:")
    print(f"  GOOGLE_CALENDAR_ID: {os.environ.get('GOOGLE_CALENDAR_ID', '(not set)')[:60]}...")
    print(f"  GOOGLE_CLIENT_ID: {'(set)' if os.environ.get('GOOGLE_CLIENT_ID') else '(not set)'}")
    print(f"  GOOGLE_CLIENT_SECRET: {'(set)' if os.environ.get('GOOGLE_CLIENT_SECRET') else '(not set)'}")
    print(f"  GOOGLE_REFRESH_TOKEN: {'(set)' if os.environ.get('GOOGLE_REFRESH_TOKEN') else '(not set)'}")
    print()

    if not calendar_client.is_configured():
        print("FAIL: Calendar not configured.")
        print("  - For OAuth: Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.")
        print("  - Run: python scripts/oauth_refresh_token.py (add redirect URI http://localhost:8766/)")
        print("  - Set GOOGLE_CALENDAR_ID to your calendar ID (e.g. c_xxx@group.calendar.google.com)")
        sys.exit(1)

    print("Connected. Testing...")
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Paris")
        today = datetime.now(tz).date()
        time_min = datetime(today.year, today.month, today.day, tzinfo=tz)
    except Exception:
        today = datetime.utcnow().date()
        time_min = datetime(today.year, today.month, today.day)
    time_max = time_min + timedelta(days=7)

    events = calendar_client.list_events(time_min=time_min, time_max=time_max)
    print(f"  Events (next 7 days): {len(events)}")
    for ev in events[:5]:
        print(f"    - {ev.get('summary')} @ {ev.get('start')}")

    # Test get_available_slots
    from datetime import date
    slot_date = datetime(today.year, today.month, today.day)
    slots = calendar_client.get_available_slots(slot_date)
    print(f"  Available slots today: {len(slots)}")
    for s in slots[:3]:
        print(f"    - {s['start'][:16]}")

    print("\nOK: Calendar works.")

if __name__ == "__main__":
    main()
