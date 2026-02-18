"""Load YAML config for intents, routing, and voice (single source of truth)."""
from pathlib import Path
from typing import Optional
import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

_voice_config: Optional[dict] = None


def load_yaml(name: str) -> dict:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_intents() -> dict:
    return load_yaml("intents")


def get_routing_rules() -> dict:
    return load_yaml("routing_rules")


def get_routing_target(intent_id: str) -> str:
    """Return routing target for an intent (e.g. in_agent, operations, reception)."""
    data = load_yaml("routing_rules")
    by_intent = (data.get("routing") or {}).get("by_intent") or {}
    return (by_intent.get(intent_id) or {}).get("target") or "reception"


def _get_voice_config() -> dict:
    global _voice_config
    if _voice_config is None:
        _voice_config = load_yaml("voice")
    return _voice_config


def get_greeting() -> str:
    """Greeting for start of call (from config/voice.yaml)."""
    c = _get_voice_config()
    return (c.get("greeting") or "").strip() or "Bonjour, vous êtes en contact avec APEN. Dites le motif de votre appel."


def get_transfer_message() -> str:
    """Message said when transferring (from config)."""
    c = _get_voice_config()
    msgs = c.get("messages") or {}
    return (msgs.get("transfer_in_progress") or "").strip() or "Je vous transfère. Merci de patienter."


def get_unclear_message() -> str:
    """Message when transcript empty or intent unclear (from config)."""
    c = _get_voice_config()
    msgs = c.get("messages") or {}
    return (msgs.get("unclear") or "").strip() or "Je n'ai pas bien compris. Un conseiller vous rappellera. Au revoir."


def get_callback_message(intent_id: str) -> str:
    """Message said when not transferring, by intent (from config)."""
    c = _get_voice_config()
    by_intent = (c.get("messages") or {}).get("callback_by_intent") or {}
    return (by_intent.get(intent_id) or by_intent.get("default") or "").strip() or "Nous avons bien noté votre demande. Un conseiller vous rappellera. Au revoir."


def get_vapi_config() -> dict:
    """Vapi assistant overrides (model, voice, system_prompt) from config."""
    c = _get_voice_config()
    return c.get("vapi") or {}
