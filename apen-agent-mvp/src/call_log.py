"""
Call log storage for dashboard: each Vapi call and what the agent did (transcript, intent, outcome, summary/appointment).
"""
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

STORAGE_PATH = Path(__file__).resolve().parent.parent / "data" / "calls.json"
_calls: list[dict] = []


def _ensure_data_dir():
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


def ensure_storage():
    _ensure_data_dir()


def _load():
    global _calls
    if _calls:
        return
    _ensure_data_dir()
    if STORAGE_PATH.exists():
        try:
            with open(STORAGE_PATH, "r", encoding="utf-8") as f:
                _calls = json.load(f)
        except (json.JSONDecodeError, IOError):
            _calls = []


def _save():
    _ensure_data_dir()
    try:
        with open(STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump(_calls, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def log_call_started(call_id: str, caller_phone: str = "") -> None:
    """Call when we receive assistant-request (call started)."""
    if not call_id:
        return
    _load()
    existing = next((c for c in _calls if c.get("call_id") == call_id), None)
    if existing:
        return
    _calls.append({
        "call_id": call_id,
        "caller_phone": caller_phone or "",
        "started_at": datetime.utcnow().isoformat() + "Z",
        "events": [],
        "summary_id": None,
        "appointment_id": None,
    })
    _save()


def log_route_result(
    call_id: str,
    transcript: str,
    intent: str,
    action: str,
    outcome: str,
    summary_id: Optional[str] = None,
    appointment_id: Optional[str] = None,
) -> None:
    """Append one apen_route result (what the caller said, intent, and what we did)."""
    if not call_id:
        return
    _load()
    call = next((c for c in _calls if c.get("call_id") == call_id), None)
    if not call:
        call = {
            "call_id": call_id,
            "caller_phone": "",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "events": [],
            "summary_id": None,
            "appointment_id": None,
        }
        _calls.append(call)
    call["events"].append({
        "transcript": (transcript or "")[:1000],
        "intent": intent,
        "action": action,
        "outcome": outcome,
    })
    if summary_id:
        call["summary_id"] = summary_id
    if appointment_id:
        call["appointment_id"] = appointment_id
    _save()


def log_appointment_booked(call_id: str, appointment_id: str) -> None:
    """Record that an appointment was created during this call."""
    if not call_id or not appointment_id:
        return
    _load()
    call = next((c for c in _calls if c.get("call_id") == call_id), None)
    if call:
        call["appointment_id"] = appointment_id
        _save()


def list_calls(limit: int = 100) -> list[dict]:
    """List recent calls (newest first)."""
    _load()
    out = list(_calls)
    out.sort(key=lambda c: c.get("started_at") or "", reverse=True)
    return out[:limit]
