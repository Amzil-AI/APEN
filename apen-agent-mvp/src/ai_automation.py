"""
AI-driven automation (e.g. calendar from callbacks). Uses OpenAI to suggest or build event titles and descriptions.
Set OPENAI_API_KEY in env.
"""
import json
import os
from typing import Optional

def _get_client():
    """Lazy OpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        return None


def suggest_calendar_event_for_callback(summary: dict) -> Optional[dict]:
    """
    Use AI to suggest a calendar event title and description from a callback summary.
    Returns {"title": str, "description": str} or None if OpenAI unavailable.
    """
    client = _get_client()
    if not client or not summary:
        return None

    caller = (summary.get("caller_name") or "Caller").strip()
    phone = (summary.get("caller_phone") or "").strip()
    reason = (summary.get("reason") or "").strip()[:500]
    site = (summary.get("site") or "paris").strip()
    urgency = (summary.get("urgency") or "medium").strip()
    notes = (summary.get("notes") or "").strip()[:300]

    system = """You are an assistant for APEN call reception. Given a callback summary, output a short calendar event title and a clear description.
Output only valid JSON with exactly two keys: "title" (short, e.g. "Rappel – Jean Dupont" or "Callback – opening hours") and "description" (multi-line if needed: Caller, Phone, Reason, Site, Designated: Reception).
Use French for title/description. Keep title under 60 characters. In description include: Caller, Phone, Reason, Site, and "Designated: Reception" so the team knows who handles it."""

    user = f"""Callback summary:
- Caller: {caller}
- Phone: {phone}
- Reason: {reason}
- Site: {site}
- Urgency: {urgency}
- Notes: {notes}

Return JSON: {{ "title": "...", "description": "..." }}"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        text = (resp.choices[0].message.content or "").strip()
        # Strip markdown code block if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0].strip()
        out = json.loads(text)
        if isinstance(out, dict) and "title" in out and "description" in out:
            return {"title": str(out["title"])[:200], "description": str(out["description"])[:2000]}
    except (json.JSONDecodeError, IndexError, KeyError, Exception):
        pass
    # Fallback without AI
    title = f"Rappel – {caller}" if caller else "Callback"
    description = f"Caller: {caller}\nPhone: {phone}\nReason: {reason}\nSite: {site}\nDesignated: Reception"
    return {"title": title[:200], "description": description[:2000]}
