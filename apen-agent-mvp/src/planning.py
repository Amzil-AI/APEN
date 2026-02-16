"""
Planning publish/send – upload, store, optional email (beyond Limova).
"""
from pathlib import Path
from typing import Optional
import uuid
from datetime import datetime

PLANNING_DIR = Path(__file__).resolve().parent.parent / "data" / "plannings"
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".html", ".png", ".jpg"}


def _ensure_dir():
    PLANNING_DIR.mkdir(parents=True, exist_ok=True)


def save_planning(file_content: bytes, filename: str) -> dict:
    """Save uploaded planning file; return id and path."""
    _ensure_dir()
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    plan_id = str(uuid.uuid4())
    safe_name = f"{plan_id}{ext}"
    path = PLANNING_DIR / safe_name
    path.write_bytes(file_content)
    return {
        "id": plan_id,
        "filename": filename,
        "stored_as": safe_name,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }


def get_planning_path(plan_id: str) -> Optional[Path]:
    """Return Path to planning file if it exists."""
    _ensure_dir()
    for ext in ALLOWED_EXTENSIONS:
        p = PLANNING_DIR / f"{plan_id}{ext}"
        if p.exists():
            return p
    return None
