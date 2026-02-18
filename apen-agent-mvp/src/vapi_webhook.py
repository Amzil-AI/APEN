"""
Vapi webhook adapter – we become the "brain" for voice calls (build Limova and more).
Fully config-driven: greeting and system prompt from config/voice.yaml.
Handles: assistant-request (return our greeting + tools), tool-calls (apen_route, apen_get_slots, apen_book_appointment),
transfer-destination-request (return number we computed for this call).
Logs each call to the dashboard (call_log).
Set your Vapi Phone Number or Assistant "Server URL" to: https://your-app.com/webhooks/vapi

Call cutting immediately: Vapi often rejects transient assistants that include inline "functions".
We return a minimal assistant (no functions) by default so the call stays up. For full routing/booking,
create an assistant in Vapi with server-side tools and set VAPI_ASSISTANT_ID, or set VAPI_INLINE_TOOLS=1 to try inline.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from . import voice
from .config_loader import get_vapi_config
from . import call_log
from . import calendar_client

# In-memory: call_id -> last apen_route result (so we can return destination on transfer-destination-request)
_pending_transfer: dict[str, dict] = {}


def get_apen_route_tool() -> dict:
    """Vapi function/tool definition for routing the call using our logic."""
    return {
        "name": "apen_route",
        "description": "Get routing for the caller. Call this with the user's message and caller phone. Returns transfer_number to dial or say_message to speak. Use first to qualify the call.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_message": {"type": "string", "description": "What the caller said"},
                "caller_phone": {"type": "string", "description": "Caller phone number"},
            },
            "required": ["user_message"],
        },
    }


def get_apen_get_slots_tool() -> dict:
    """Get available appointment slots for a date (for in-call booking)."""
    return {
        "name": "apen_get_slots",
        "description": "Get available appointment slots for a given date. Call this when the caller wants to book an appointment. date format: YYYY-MM-DD.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date for slots, YYYY-MM-DD (e.g. 2026-02-20). If omitted, use tomorrow."},
            },
            "required": [],
        },
    }


def get_apen_book_appointment_tool() -> dict:
    """Book an appointment in the calendar (for in-call booking)."""
    return {
        "name": "apen_book_appointment",
        "description": "Book an appointment. Call this after the caller chose a slot. start_iso and end_iso must match one of the slots from apen_get_slots (e.g. 2026-02-20T10:00:00, 2026-02-20T10:30:00).",
        "parameters": {
            "type": "object",
            "properties": {
                "start_iso": {"type": "string", "description": "Slot start in ISO format (e.g. 2026-02-20T10:00:00)"},
                "end_iso": {"type": "string", "description": "Slot end in ISO format (e.g. 2026-02-20T10:30:00)"},
                "subject": {"type": "string", "description": "Appointment subject (e.g. Uniform collection)"},
                "email": {"type": "string", "description": "Caller email if they gave it (optional)"},
            },
            "required": ["start_iso", "end_iso", "subject"],
        },
    }


def handle_assistant_request(call: Optional[dict] = None) -> dict:
    """Return Vapi assistant config. Uses VAPI_ASSISTANT_ID if set; else minimal assistant (no inline functions) so the call does not cut."""
    caller_phone = ""
    if call and isinstance(call.get("customer"), dict):
        caller_phone = (call["customer"].get("number") or "") or ""
    call_id = (call or {}).get("id") or ""
    if call_id:
        call_log.log_call_started(call_id, caller_phone)

    # If you created an assistant in Vapi with server-side tools, return its ID so the call uses it (no inline functions = no drop).
    assistant_id = os.environ.get("VAPI_ASSISTANT_ID", "").strip()
    if assistant_id:
        return {"assistantId": assistant_id}

    first_message = (voice.get_greeting_text() or "").strip().replace("\n", " ").strip() or "Bonjour, vous êtes en contact avec APEN."
    vapi_cfg = get_vapi_config()
    model_name = (vapi_cfg.get("model") or "gpt-4o-mini").strip()
    voice_provider = (vapi_cfg.get("voice_provider") or "11labs").strip()
    voice_id = (vapi_cfg.get("voice_id") or "rachel").strip()

    # Inline "functions" in transient assistant often cause Vapi to reject and drop the call. We only add them if explicitly enabled.
    use_inline_tools = os.environ.get("VAPI_INLINE_TOOLS", "").strip().lower() in ("1", "true", "yes")

    if use_inline_tools:
        system_prompt = (vapi_cfg.get("system_prompt") or "").strip() or (
            "You are APEN's voice agent. "
            "1) First, when the user states their reason for calling, call apen_route with their message and caller_phone. "
            "2) If the result says intent is 'appointment' and action is 'book_appointment': call apen_get_slots, then tell the user the slots and ask which one; when they choose, call apen_book_appointment. "
            "3) If the result has transfer_number, use the transferCall tool and say the say_message. "
            "4) If only say_message is set (callback), say it and end the call. Be brief. Language: French."
        )
        model_block = {
            "provider": "openai",
            "model": model_name,
            "messages": [{"role": "system", "content": system_prompt}],
            "functions": [get_apen_route_tool(), get_apen_get_slots_tool(), get_apen_book_appointment_tool()],
        }
    else:
        # Minimal assistant: no functions, so Vapi accepts and the call stays connected.
        system_prompt = (
            "You are APEN's voice reception agent. Greet the caller and ask how you can help. "
            "Tell them their request will be noted and a colleague will call them back. Be brief and professional. Language: French."
        )
        model_block = {
            "provider": "openai",
            "model": model_name,
            "messages": [{"role": "system", "content": system_prompt}],
        }

    return {
        "assistant": {
            "firstMessage": first_message,
            "model": model_block,
            "voice": {"provider": voice_provider, "voiceId": voice_id},
        }
    }


def handle_tool_calls(
    tool_call_list: list,
    call: Optional[dict] = None,
) -> dict:
    """
    Handle tool-calls from Vapi: apen_route, apen_get_slots, apen_book_appointment.
    """
    caller_phone = ""
    if call and isinstance(call.get("customer"), dict):
        caller_phone = (call["customer"].get("number") or "") or ""
    call_id = (call or {}).get("id") or ""

    results = []
    for tc in tool_call_list or []:
        name = tc.get("name") or tc.get("function", {}).get("name")
        tid = tc.get("id")
        params = tc.get("parameters") or tc.get("function", {}).get("arguments") or {}
        if isinstance(params, str):
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
                "summary_id": out.get("summary_id"),
            }
            if call_id:
                _pending_transfer[call_id] = result
                call_log.log_route_result(
                    call_id,
                    transcript=user_message,
                    intent=out.get("intent", ""),
                    action=out.get("action", ""),
                    outcome=out.get("response_type", "callback"),
                    summary_id=out.get("summary_id"),
                )
            results.append({"name": "apen_route", "toolCallId": tid, "result": result})

        elif name == "apen_get_slots":
            date_str = (params.get("date") or "").strip()
            if date_str:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    dt = datetime.now() + timedelta(days=1)
            else:
                dt = datetime.now() + timedelta(days=1)
            slots = calendar_client.get_available_slots(dt)
            slot_lines = []
            for i, s in enumerate(slots, 1):
                start = s.get("start", "")[:19].replace("T", " ")
                end = s.get("end", "")[11:16]
                slot_lines.append(f"{i}) {start} - {end}")
            result = {
                "date": dt.strftime("%Y-%m-%d"),
                "slots": slots,
                "message": f"Available slots on {dt.strftime('%Y-%m-%d')}: " + "; ".join(slot_lines) if slot_lines else "No slots available.",
            }
            results.append({"name": "apen_get_slots", "toolCallId": tid, "result": result})

        elif name == "apen_book_appointment":
            start_iso = (params.get("start_iso") or "").strip()
            end_iso = (params.get("end_iso") or "").strip()
            subject = (params.get("subject") or "Rendez-vous").strip() or "Rendez-vous"
            email = (params.get("email") or "").strip() or None
            if not start_iso or not end_iso:
                result = {"success": False, "message": "Missing start_iso or end_iso."}
            else:
                ev = calendar_client.create_appointment(start_iso, end_iso, subject, "", attendee_email=email)
                if ev:
                    result = {"success": True, "appointment_id": ev.get("id"), "message": f"Rendez-vous confirmé: {subject} le {start_iso[:10]} à {start_iso[11:16]}."}
                    if call_id:
                        call_log.log_appointment_booked(call_id, ev.get("id", ""))
                else:
                    result = {"success": False, "message": "Calendar not configured or booking failed."}
            results.append({"name": "apen_book_appointment", "toolCallId": tid, "result": result})

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
    Accepts both shapes: body.message.type or body.type (Vapi can send either). Also accepts camelCase (assistantRequest).
    """
    import logging
    log = logging.getLogger("apen-agent-mvp.vapi")

    msg = body.get("message") if "message" in body else body
    msg = msg or {}
    typ = (msg.get("type") or body.get("type") or "").strip()
    if not typ and "message" in body:
        typ = (body.get("message", {}).get("type") or "").strip()
    # Vapi may send assistant-request or assistantRequest
    if typ == "assistantRequest":
        typ = "assistant-request"
    call = msg.get("call") or body.get("call")

    if typ == "assistant-request":
        log.info("Vapi assistant-request received")
        return handle_assistant_request(call)
    if typ == "tool-calls":
        tool_list = msg.get("toolCallList") or msg.get("tool_call_list") or []
        return handle_tool_calls(tool_list, call)
    if typ == "transfer-destination-request":
        return handle_transfer_destination_request(call)

    if typ or body:
        log.warning("Vapi webhook unhandled message type: %s (keys: %s)", typ or "(empty)", list(body.keys()))
    return None
