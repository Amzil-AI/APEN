"""
Callback summary storage for MVP. In-memory + optional JSON file persistence.
In production, replace with DB or Limova webhook persistence.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import uuid

STORAGE_PATH = Path(__file__).resolve().parent.parent / "data" / "callback_summaries.json"
_summaries: list[dict] = []


def _ensure_data_dir():
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


def ensure_storage():
    """Ensure data directory exists (call at startup)."""
    _ensure_data_dir()


def _load():
    global _summaries
    if _summaries:
        return
    _ensure_data_dir()
    if STORAGE_PATH.exists():
        try:
            with open(STORAGE_PATH, "r", encoding="utf-8") as f:
                _summaries = json.load(f)
        except (json.JSONDecodeError, IOError):
            _summaries = []


def _save():
    _ensure_data_dir()
    try:
        with open(STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump(_summaries, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def add_summary(
    caller_name: str,
    caller_phone: str,
    reason: str,
    site: str = "paris",
    urgency: str = "medium",
    callback_preference: Optional[str] = None,
    notes: Optional[str] = None,
    call_id: Optional[str] = None,
) -> dict:
    """Append a callback summary and return it with id and timestamp."""
    _load()
    entry = {
        "id": call_id or str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "caller_name": caller_name,
        "caller_phone": caller_phone,
        "reason": reason,
        "site": site,
        "urgency": urgency,
        "callback_preference": callback_preference or "asap",
        "notes": notes or "",
        "status": "pending",  # pending | called | closed
    }
    _summaries.append(entry)
    _save()
    return entry


def list_summaries(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    """List summaries, optionally filtered by status (pending, called, closed)."""
    _load()
    out = list(_summaries)
    if status:
        out = [s for s in out if s.get("status") == status]
    out.reverse()  # newest first
    return out[:limit]


def get_summary(summary_id: str) -> Optional[dict]:
    _load()
    for s in _summaries:
        if s.get("id") == summary_id:
            return s
    return None


def update_status(summary_id: str, status: str) -> Optional[dict]:
    """Update status to 'called' or 'closed'."""
    _load()
    for s in _summaries:
        if s.get("id") == summary_id:
            s["status"] = status
            _save()
            return s
    return None


def update_notes(summary_id: str, notes: str, append: bool = False) -> Optional[dict]:
    """Set or append notes on a callback summary (e.g. full transcript after call ended)."""
    _load()
    for s in _summaries:
        if s.get("id") == summary_id:
            if append and s.get("notes"):
                s["notes"] = (s.get("notes") or "").strip() + "\n\n" + (notes or "").strip()
            else:
                s["notes"] = (notes or "").strip()
            _save()
            return s
    return None
