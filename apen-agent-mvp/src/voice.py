"""
Voice layer – provider-agnostic (no Twilio). Fully config-driven from config/voice.yaml.
Any voice platform (Vapi, Bland, SIP gateway, etc.) can call our API with transcript + caller;
we return intent, routing, transfer number or message to say, and we create callback summaries when needed.
Uses AI for intent and callback summary extraction when OPENAI_API_KEY is set.
"""
from typing import Optional

from . import intent
from . import summary_store
try:
    from . import ai_intent as _ai_intent
except ImportError:
    _ai_intent = None  # type: ignore
from .config_loader import (
    get_routing_rules,
    get_routing_target,
    get_greeting as _cfg_greeting,
    get_transfer_message as _cfg_transfer_msg,
    get_unclear_message as _cfg_unclear_msg,
    get_callback_message as _cfg_callback_msg,
)

DEFAULT_SITE = "paris"


def get_greeting_text() -> str:
    """Greeting for the start of the call (from config/voice.yaml)."""
    return _cfg_greeting()


def get_transfer_number(intent_id: str, site: Optional[str] = None) -> Optional[str]:
    """Return the phone number to transfer to for this intent and site, or None if in_agent."""
    target = get_routing_target(intent_id)
    if target == "in_agent":
        return None
    data = get_routing_rules()
    by_site = (data.get("routing") or {}).get("by_site") or {}
    site = site or (data.get("routing") or {}).get("default_site") or DEFAULT_SITE
    numbers = by_site.get(site) or by_site.get(DEFAULT_SITE) or {}
    num = numbers.get(target)
    if num and num != "+33XXXXXXXX":
        return num
    return None


def _say_message_for_intent(intent_id: str) -> str:
    """Message to say when not transferring (from config/voice.yaml)."""
    return _cfg_callback_msg(intent_id)


def process_speech(transcript: str, caller_phone: str = "", site: Optional[str] = None, language: str = "fr") -> dict:
    """
    Process caller speech: detect intent, return instructions for any voice provider.
    Creates a callback summary when not transferring.
    Returns:
      - intent, action, routing_target
      - response_type: "transfer" | "callback"
      - transfer_number: number to dial (if response_type=transfer), else null
      - say_message: text to speak (if response_type=callback)
    """
    transcript = (transcript or "").strip()
    if not transcript:
        return {
            "intent": "other",
            "action": "collect_summary",
            "routing_target": "reception",
            "response_type": "callback",
            "transfer_number": None,
            "say_message": _cfg_unclear_msg(),
        }

    intent_id = intent.detect_intent_with_ai(transcript, language or "fr")
    action = intent.get_intent_action(intent_id)
    target = get_routing_target(intent_id)
    transfer_number = get_transfer_number(intent_id, site)

    if transfer_number:
        return {
            "intent": intent_id,
            "action": action,
            "routing_target": target,
            "response_type": "transfer",
            "transfer_number": transfer_number,
            "say_message": _cfg_transfer_msg(),
        }

    # No transfer: build summary (AI-extracted if available) and return message to say
    caller_name = "Appelant"
    reason = transcript[:500]
    summary_urgency = "medium"
    summary_site = site or DEFAULT_SITE
    if _ai_intent:
        extracted = _ai_intent.extract_callback_summary_ai(transcript, caller_phone or "")
        if extracted:
            caller_name = extracted.get("caller_name") or caller_name
            reason = extracted.get("reason") or reason
            summary_urgency = extracted.get("urgency") or summary_urgency
            summary_site = extracted.get("site") or summary_site
    entry = summary_store.add_summary(
        caller_name=caller_name,
        caller_phone=caller_phone or "Inconnu",
        reason=reason,
        site=summary_site,
        urgency=summary_urgency,
        call_id=f"voice-{intent_id}",
    )
    return {
        "intent": intent_id,
        "action": action,
        "routing_target": target,
        "response_type": "callback",
        "transfer_number": None,
        "say_message": _say_message_for_intent(intent_id),
        "summary_id": entry.get("id"),
    }
