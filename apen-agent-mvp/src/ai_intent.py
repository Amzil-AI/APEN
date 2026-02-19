"""
AI-based intent detection and callback summary extraction.
Uses OpenAI when OPENAI_API_KEY is set; callers fall back to rule-based / defaults otherwise.
"""
import json
import os
from typing import Optional

from .config_loader import get_intents


def _get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        return None


# Valid intent ids (must match config)
VALID_INTENTS = {"appointment", "callback", "info", "emergency", "after_sales", "partner", "other"}


def detect_intent_ai(message: str, language: str = "fr") -> Optional[str]:
    """
    Use AI to classify the caller message into one intent.
    Returns intent id or None if AI unavailable / error (caller should use keyword fallback).
    """
    if not message or not message.strip():
        return "other"
    client = _get_client()
    if not client:
        return None
    data = get_intents()
    intents = data.get("intents", {})
    # Build short list for the prompt
    lines = []
    for iid, config in intents.items():
        if iid == "other":
            continue
        name = config.get("name") or iid
        desc = (config.get("description") or "")[:80]
        lines.append(f"- {iid}: {name}. {desc}")
    intents_list = "\n".join(lines)
    lang_instruction = "Answer with exactly one word from the list below (the intent id)." if language == "en" else "Réponds par un seul mot de la liste ci-dessous (l'id d'intention)."
    system = f"""You are a call classifier for APEN. Given the caller's message, choose the single best intent.

Valid intents (reply with exactly one word):
{intents_list}
- other: anything else, unclassified

{lang_instruction}"""
    user = message.strip()[:800]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.1,
            max_tokens=20,
        )
        text = (resp.choices[0].message.content or "").strip().lower().split()[0] if resp.choices else ""
        # Remove punctuation
        text = "".join(c for c in text if c.isalnum() or c == "_")
        if text in VALID_INTENTS:
            return text
        return "other"
    except Exception:
        return None


def extract_callback_summary_ai(transcript: str, caller_phone: str = "") -> Optional[dict]:
    """
    Use AI to extract structured callback summary from transcript.
    Returns dict with caller_name, reason, urgency (low|medium|high), site (e.g. paris)
    or None if AI unavailable / error.
    """
    if not transcript or not transcript.strip():
        return None
    client = _get_client()
    if not client:
        return None
    system = """You extract structured fields from a call transcript for a callback summary.
Output valid JSON only, with exactly these keys:
- caller_name: string (name if mentioned, else "Appelant")
- reason: string (short reason for callback, 1-2 sentences, in the same language as the transcript)
- urgency: one of "low", "medium", "high"
- site: string, one of "paris", "lyon", "marseille", "toulouse", or "paris" if unknown

No markdown, no explanation. Example: {"caller_name":"Jean Dupont","reason":"Demande d'horaires et adresse.","urgency":"medium","site":"paris"}"""
    user = (transcript[:1500] + ("\nCaller phone: " + caller_phone if caller_phone else "")).strip()
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            max_tokens=300,
        )
        text = (resp.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0].strip()
        out = json.loads(text)
        if not isinstance(out, dict):
            return None
        name = (out.get("caller_name") or "Appelant").strip() or "Appelant"
        reason = (out.get("reason") or transcript[:500]).strip() or transcript[:500]
        urgency = (out.get("urgency") or "medium").strip().lower()
        if urgency not in ("low", "medium", "high"):
            urgency = "medium"
        site = (out.get("site") or "paris").strip().lower() or "paris"
        return {
            "caller_name": name[:200],
            "reason": reason[:500],
            "urgency": urgency,
            "site": site[:50],
        }
    except (json.JSONDecodeError, KeyError, Exception):
        return None
