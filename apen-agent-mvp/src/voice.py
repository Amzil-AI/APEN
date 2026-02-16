"""
Voice layer – provider-agnostic (no Twilio).
Any voice platform (Vapi, Bland, SIP gateway, etc.) can call our API with transcript + caller;
we return intent, routing, transfer number or message to say, and we create callback summaries when needed.
"""
from typing import Optional

from . import intent
from .config_loader import get_routing_rules, get_routing_target
from . import summary_store

DEFAULT_SITE = "paris"


def get_greeting_text() -> str:
    """Greeting for the start of the call (any provider can use this for TTS)."""
    return (
        "Bonjour, vous êtes en contact avec APEN. "
        "Dites brièvement le motif de votre appel : rendez-vous, information, urgence, ou autre."
    )


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
    """French message to say when not transferring (callback)."""
    if intent_id == "appointment":
        return "Pour la prise de rendez-vous, un conseiller vous rappellera sous peu. Au revoir."
    if intent_id == "info":
        return "Un conseiller vous rappellera pour vous donner les informations. Au revoir."
    return "Nous avons bien noté votre demande. Un conseiller vous rappellera. Au revoir."


def process_speech(transcript: str, caller_phone: str = "", site: Optional[str] = None) -> dict:
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
            "say_message": "Je n'ai pas bien compris. Un conseiller vous rappellera. Au revoir.",
        }

    intent_id = intent.detect_intent(transcript, "fr")
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
            "say_message": "Je vous transfère. Merci de patienter.",
        }

    # No transfer: store summary and return message to say
    summary_store.add_summary(
        caller_name="Appelant",
        caller_phone=caller_phone or "Inconnu",
        reason=transcript[:500],
        site=site or DEFAULT_SITE,
        urgency="medium",
        call_id=f"voice-{intent_id}",
    )
    return {
        "intent": intent_id,
        "action": action,
        "routing_target": target,
        "response_type": "callback",
        "transfer_number": None,
        "say_message": _say_message_for_intent(intent_id),
    }
