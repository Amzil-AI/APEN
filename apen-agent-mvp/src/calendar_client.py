"""
Google Calendar integration for appointment booking (MVP).
Uses a service account or OAuth; set GOOGLE_CALENDAR_ID and credentials path in env.
"""
from datetime import datetime, timedelta
from typing import Optional
import os

# Optional: only load if credentials available
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
# For MVP, we support service account JSON path
CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
# Business hours and slot times are in this timezone
TIMEZONE = os.environ.get("GOOGLE_CALENDAR_TIMEZONE", "Europe/Paris")


def _get_service():
    if not HAS_GOOGLE or not CREDENTIALS_PATH or not os.path.exists(CREDENTIALS_PATH):
        return None
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds)


def is_configured() -> bool:
    """True if Google Calendar credentials and calendar ID are set and usable."""
    return _get_service() is not None and bool(CALENDAR_ID)


def _day_range_paris(date: datetime) -> tuple[datetime, datetime]:
    """Return (day_start, day_end) for the given date in Europe/Paris (9:00–18:00)."""
    y, m, d = date.year, date.month, date.day
    if ZoneInfo:
        tz = ZoneInfo(TIMEZONE)
        day_start = datetime(y, m, d, 9, 0, 0, tzinfo=tz)
        day_end = datetime(y, m, d, 18, 0, 0, tzinfo=tz)
        return day_start, day_end
    day_start = date.replace(hour=9, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=18, minute=0, second=0, microsecond=0)
    return day_start, day_end


def get_available_slots(
    date: datetime,
    duration_minutes: int = 30,
    business_start: int = 9,
    business_end: int = 18,
    slot_interval: int = 30,
) -> list[dict]:
    """
    Return list of slot dicts {start, end} in ISO format for the given date.
    Uses Europe/Paris for business hours when available. Excludes slots that
    overlap existing events (if calendar is configured).
    """
    service = _get_service()
    day_start, day_end = _day_range_paris(date)
    slots = []
    current = day_start

    while current + timedelta(minutes=duration_minutes) <= day_end:
        slot_end = current + timedelta(minutes=duration_minutes)
        slots.append({
            "start": current.isoformat(),
            "end": slot_end.isoformat(),
        })
        current += timedelta(minutes=slot_interval)

    if service and CALENDAR_ID:
        try:
            time_min = day_start.isoformat() if day_start.tzinfo else day_start.isoformat() + "Z"
            time_max = day_end.isoformat() if day_end.tzinfo else day_end.isoformat() + "Z"
            events = (
                service.events()
                .list(
                    calendarId=CALENDAR_ID,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                )
                .execute()
            )
            busy_ranges = []
            for ev in events.get("items", []):
                start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
                end = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
                if start and end:
                    busy_ranges.append((start, end))
            # Filter out slots that overlap any busy range
            def overlaps(slot: dict) -> bool:
                for b_start, b_end in busy_ranges:
                    if slot["start"] < b_end and slot["end"] > b_start:
                        return True
                return False
            slots = [s for s in slots if not overlaps(s)]
        except HttpError:
            pass  # Return all slots if calendar list fails

    return slots[:10]  # Return at most 10 slots for MVP


def list_events(
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    max_results: int = 50,
) -> list[dict]:
    """
    List calendar events in the given time range. Returns list of dicts with
    id, summary, description, start, end, htmlLink.
    """
    service = _get_service()
    if not service or not CALENDAR_ID:
        return []
    if time_min is None:
        time_min = datetime.utcnow()
    if time_max is None:
        time_max = time_min + timedelta(days=14)
    try:
        events_result = (
            service.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=time_min.isoformat() + "Z" if not time_min.tzinfo else time_min.isoformat(),
                timeMax=time_max.isoformat() + "Z" if not time_max.tzinfo else time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=max_results,
            )
            .execute()
        )
        out = []
        for ev in events_result.get("items", []):
            start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
            end = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
            out.append({
                "id": ev.get("id"),
                "summary": ev.get("summary") or "(No title)",
                "description": (ev.get("description") or "").strip(),
                "start": start,
                "end": end,
                "htmlLink": ev.get("htmlLink"),
            })
        return out
    except HttpError:
        return []


def create_appointment(
    start_iso: str,
    end_iso: str,
    summary: str,
    description: str = "",
    attendee_email: Optional[str] = None,
) -> Optional[dict]:
    """Create a calendar event. Returns event dict or None on failure."""
    service = _get_service()
    if not service:
        return None

    body = {
        "summary": summary,
        "description": description or "APEN – Prise de rendez-vous (agent IA)",
        "start": {"dateTime": start_iso, "timeZone": "Europe/Paris"},
        "end": {"dateTime": end_iso, "timeZone": "Europe/Paris"},
    }
    if attendee_email:
        body["attendees"] = [{"email": attendee_email}]

    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=body).execute()
        return {"id": event.get("id"), "htmlLink": event.get("htmlLink"), "start": start_iso, "end": end_iso}
    except HttpError:
        return None
