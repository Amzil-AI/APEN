"""Intent detection from caller message (rule-based for MVP)."""
from .config_loader import get_intents


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


def get_intent_action(intent_id: str) -> str:
    """Return action for intent: book_appointment, provide_info, transfer, collect_summary."""
    data = get_intents()
    intents = data.get("intents", {})
    config = intents.get(intent_id, {})
    return config.get("action", "collect_summary")
