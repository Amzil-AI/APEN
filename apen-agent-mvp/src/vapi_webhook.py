"""
Vapi webhook adapter – we become the "brain" for voice calls (build Limova and more).
Fully config-driven: greeting and system prompt from config/voice.yaml.
Handles: assistant-request (return our greeting + apen_route tool), tool-calls (apen_route → our voice.process_speech),
transfer-destination-request (return number we computed for this call).
Set your Vapi Phone Number or Assistant "Server URL" to: https://your-app.com/webhooks/vapi
"""
from typing import Any, Optional

from . import voice
from .config_loader import get_vapi_config

# In-memory: call_id -> last apen_route result (so we can return destination on transfer-destination-request)
_pending_transfer: dict[str, dict] = {}


def get_apen_route_tool() -> dict:
    """Vapi function/tool definition for routing the call using our logic."""
    return {
        "name": "apen_route",
        "description": "Get routing for the caller. Call this with the user's message and caller phone. Returns transfer_number to dial or say_message to speak.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_message": {"type": "string", "description": "What the caller said"},
                "caller_phone": {"type": "string", "description": "Caller phone number"},
            },
            "required": ["user_message"],
        },
    }


def handle_assistant_request(call: Optional[dict] = None) -> dict:
    """Return Vapi assistant config from config/voice.yaml: greeting + apen_route tool."""
    caller_phone = ""
    if call and isinstance(call.get("customer"), dict):
        caller_phone = (call["customer"].get("number") or "") or ""
    first_message = voice.get_greeting_text()
    vapi_cfg = get_vapi_config()
    system_prompt = (vapi_cfg.get("system_prompt") or "").strip() or (
        "You are APEN's voice agent. When the user states their reason for calling, "
        "call the apen_route function with their message and caller_phone. "
        "When you receive the result: if transfer_number is set, use the transferCall tool to transfer to that number and say the say_message. "
        "If only say_message is set, say it to the user and end the call. Be brief and professional. Language: French."
    )
    model_name = (vapi_cfg.get("model") or "gpt-4o-mini").strip()
    voice_provider = (vapi_cfg.get("voice_provider") or "11labs").strip()
    voice_id = (vapi_cfg.get("voice_id") or "rachel").strip()
    return {
        "assistant": {
            "firstMessage": first_message,
            "model": {
                "provider": "openai",
                "model": model_name,
                "messages": [{"role": "system", "content": system_prompt}],
                "functions": [get_apen_route_tool()],
            },
            "voice": {"provider": voice_provider, "voiceId": voice_id},
        }
    }


def handle_tool_calls(
    tool_call_list: list,
    call: Optional[dict] = None,
) -> dict:
    """
    Handle tool-calls from Vapi. For apen_route we call our voice.process_speech and return result.
    """
    caller_phone = ""
    if call and isinstance(call.get("customer"), dict):
        caller_phone = (call["customer"].get("number") or "") or ""

    results = []
    for tc in tool_call_list or []:
        name = tc.get("name") or tc.get("function", {}).get("name")
        tid = tc.get("id")
        params = tc.get("parameters") or tc.get("function", {}).get("arguments") or {}
        if isinstance(params, str):
            import json
            try:
                params = json.loads(params)
            except Exception:
                params = {}
        if name == "apen_route":
            user_message = (params.get("user_message") or params.get("userMessage") or "").strip()
            phone = (params.get("caller_phone") or params.get("callerPhone") or caller_phone or "").strip()
            out = voice.process_speech(user_message, phone, None)
            result = {
                "action": out.get("response_type", "callback"),
                "intent": out.get("intent"),
                "routing_target": out.get("routing_target"),
                "transfer_number": out.get("transfer_number"),
                "say_message": out.get("say_message"),
            }
            call_id = (call or {}).get("id") or ""
            if call_id:
                _pending_transfer[call_id] = result
            results.append({
                "name": "apen_route",
                "toolCallId": tid,
                "result": result,
            })
        else:
            results.append({"name": name, "toolCallId": tid, "result": {"ignored": True}})

    return {"results": results}


def handle_transfer_destination_request(call: Optional[dict] = None) -> Optional[dict]:
    """Return transfer destination from last apen_route result for this call."""
    call_id = (call or {}).get("id") or ""
    pending = _pending_transfer.pop(call_id, None) if call_id else None
    if pending and pending.get("transfer_number"):
        return {
            "destination": {"type": "number", "number": pending["transfer_number"]},
            "message": {"type": "request-start", "message": pending.get("say_message") or "Transfert en cours."},
        }
    return None


def handle_vapi_message(body: dict) -> Optional[dict]:
    """
    Dispatch Vapi webhook body. Returns response dict for assistant-request, tool-calls; None for others.
    """
    msg = body.get("message") or {}
    typ = msg.get("type")
    call = msg.get("call") or body.get("call")

    if typ == "assistant-request":
        return handle_assistant_request(call)
    if typ == "tool-calls":
        tool_list = msg.get("toolCallList") or msg.get("tool_call_list") or []
        return handle_tool_calls(tool_list, call)
    if typ == "transfer-destination-request":
        return handle_transfer_destination_request(call)

    return None
