"""Intent detection from caller message. Uses AI when OPENAI_API_KEY is set, else rule-based keywords."""
from .config_loader import get_intents

try:
    from . import ai_intent
    _has_ai = True
except ImportError:
    _has_ai = False


def detect_intent(message: str, language: str = "fr") -> str:
    """
    Detect intent from text. Returns intent id: appointment, info, emergency,
    after_sales, partner, or other.
    """
    if not message or not message.strip():
        return "other"

    data = get_intents()
    intents = data.get("intents", {})
    text = message.lower().strip()

    for intent_id, config in intents.items():
        if intent_id == "other":
            continue
        keywords = config.get(f"keywords_{language}", []) or config.get("keywords_fr", [])
        for kw in keywords:
            if kw and kw.lower() in text:
                return intent_id

    return "other"


def detect_intent_with_ai(message: str, language: str = "fr") -> str:
    """Detect intent using AI when available, otherwise keyword-based. Same return shape as detect_intent."""
    if not message or not message.strip():
        return "other"
    if _has_ai:
        ai_id = ai_intent.detect_intent_ai(message, language or "fr")
        if ai_id:
            return ai_id
    return detect_intent(message, language)


def get_intent_action(intent_id: str) -> str:
    """Return action for intent: book_appointment, provide_info, transfer, collect_summary."""
    data = get_intents()
    intents = data.get("intents", {})
    config = intents.get(intent_id, {})
    return config.get("action", "collect_summary")
