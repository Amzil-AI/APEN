"""Load YAML config for intents and routing."""
from pathlib import Path
import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


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
