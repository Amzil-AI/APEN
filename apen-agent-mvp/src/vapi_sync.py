"""
Automatic VAPI call sync - fetches calls from VAPI API and syncs to local dashboard.

Flow:
1) Fetch calls from VAPI API
2) Download recording
3) Transcribe with our external transcriber pipeline (OpenAI/Deepgram)
4) Run intent + summary flow
5) Optionally auto-book appointment slots for appointment intents
"""
import os
import logging
import tempfile
from datetime import datetime, timedelta
from typing import Optional

import requests

from . import call_log, voice, transcribe, calendar_client

log = logging.getLogger("apen-agent-mvp.vapi_sync")

TRANSCRIBE_PROVIDER = (os.environ.get("CALL_SYNC_TRANSCRIBER") or "openai").strip().lower()

def fetch_vapi_calls(limit=20):
    """Fetch recent calls from VAPI API"""
    vapi_api_key = os.environ.get("VAPI_PRIVATE_KEY", "").strip()
    if not vapi_api_key:
        log.warning("VAPI_PRIVATE_KEY not set, cannot sync calls")
        return []
    
    headers = {
        "Authorization": f"Bearer {vapi_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"https://api.vapi.ai/call?limit={limit}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            calls = response.json()
            log.info(f"Fetched {len(calls)} calls from VAPI API")
            return calls
        else:
            log.error(f"VAPI API error: {response.status_code}")
            return []
    except Exception as e:
        log.error(f"Error fetching VAPI calls: {e}")
        return []

def download_recording(url: str) -> Optional[str]:
    """Download recording to temp file, return path"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                return tmp.name
        return None
    except Exception as e:
        log.error(f"Error downloading recording: {e}")
        return None


def _transcribe_with_deepgram(audio_path: str, language: str = "fr") -> str:
    """
    Optional alternate transcriber using Deepgram REST API.
    Requires DEEPGRAM_API_KEY.
    """
    api_key = os.environ.get("DEEPGRAM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY not set")

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    resp = requests.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": "nova-2", "smart_format": "true", "language": language or "fr"},
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/wav",
        },
        data=audio_bytes,
        timeout=60,
    )
    if not resp.ok:
        raise ValueError(f"Deepgram failed: {resp.status_code} {resp.text[:200]}")

    payload = resp.json()
    try:
        return (
            payload["results"]["channels"][0]["alternatives"][0].get("transcript", "").strip()
        )
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Deepgram response parse error: {e}") from e


def _extract_text_fallback(call: dict) -> str:
    """Fallback text extraction from VAPI payload when recording transcription is unavailable."""
    transcript = (call.get("transcript") or "").strip()
    if transcript:
        return transcript

    artifact = call.get("artifact") or {}
    if isinstance(artifact, dict):
        art_transcript = (artifact.get("transcript") or "").strip()
        if art_transcript:
            return art_transcript

    messages = call.get("messages") or []
    if isinstance(messages, list):
        lines = []
        for m in messages:
            if not isinstance(m, dict):
                continue
            role = (m.get("role") or "").strip().lower()
            msg = (m.get("message") or "").strip()
            if msg and role in {"user", "assistant"}:
                lines.append(f"{role.capitalize()}: {msg}")
        if lines:
            return "\n".join(lines)

    return ""


def _transcribe_recording(recording_url: str, language: str = "fr") -> str:
    """Primary transcript path from recording using configured transcriber provider."""
    audio_file = download_recording(recording_url)
    if not audio_file:
        return ""
    try:
        if TRANSCRIBE_PROVIDER == "deepgram":
            return _transcribe_with_deepgram(audio_file, language=language)
        # Default: OpenAI Whisper (existing implementation)
        return transcribe.transcribe_audio(audio_file, language=language)
    finally:
        try:
            os.unlink(audio_file)
        except Exception:  # noqa: BLE001
            pass


def _try_auto_book_appointment(vapi_call_id: str, phone: str, transcript: str, result: dict) -> Optional[str]:
    """
    For appointment intents, try to auto-book first available slot like the test voice flow.
    Returns appointment_id when booked, else None.
    """
    if result.get("intent") != "appointment" or result.get("action") != "book_appointment":
        return None

    tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    slots = calendar_client.get_available_slots(tomorrow)
    if not slots:
        return None

    slot = slots[0]
    subject = "Uniform collection (VAPI sync)"
    desc_parts = ["APEN - Appointment from VAPI synced call"]
    if transcript.strip():
        desc_parts.append("Reason: " + transcript.strip()[:300])
    if phone.strip():
        desc_parts.append("Caller: " + phone.strip())
    ev = calendar_client.create_appointment(
        slot["start"],
        slot["end"],
        subject,
        "\n".join(desc_parts),
        attendee_email=None,
    )
    if ev and ev.get("id"):
        call_log.log_appointment_booked(vapi_call_id, ev["id"])
        return ev["id"]
    return None

def sync_call(call: dict) -> bool:
    """Sync one VAPI call to local database"""
    call_id = call.get("id", "")
    vapi_call_id = f"vapi-{call_id}"
    
    # Check if already synced
    existing = call_log.get_call(vapi_call_id)
    if existing:
        return False
    
    customer = call.get("customer", {})
    phone = customer.get("number", "") if isinstance(customer, dict) else ""
    
    log.info(f"Syncing VAPI call {call_id[:20]}... from {phone}")
    
    # Only process completed calls
    if (call.get("status") or "").lower() != "ended":
        return False

    # 1) Primary source: call recording -> external transcriber
    transcript = ""
    recording_url = call.get("recordingUrl", "")
    if recording_url:
        try:
            transcript = _transcribe_recording(recording_url, language="fr")
            if transcript:
                log.info("External transcription complete for %s", call_id[:20])
        except Exception as e:  # noqa: BLE001
            log.error("External transcription failed for %s: %s", call_id[:20], e)

    # 2) Fallbacks: VAPI transcript/artifact/messages
    if not transcript:
        transcript = _extract_text_fallback(call)

    if not transcript:
        log.warning("Skipping call %s: no transcript available after transcription/fallback", call_id[:20])
        return False
    
    # Create call log entry
    call_log.log_call_started(vapi_call_id, phone)
    
    # Process through voice system to get intent
    if transcript != "[No transcript available]":
        try:
            result = voice.process_speech(transcript, phone, None, "fr")
            
            outcome = result.get("response_type", "callback")
            appointment_id = _try_auto_book_appointment(vapi_call_id, phone, transcript, result)
            if appointment_id:
                outcome = "appointment_booked"

            call_log.log_route_result(
                vapi_call_id,
                transcript=transcript,
                intent=result.get("intent", "other"),
                action=result.get("action", ""),
                outcome=outcome,
                summary_id=result.get("summary_id"),
                appointment_id=appointment_id,
            )
            
            log.info(f"Processed call intent: {result.get('intent', 'other')}")
        except Exception as e:
            log.error(f"Error processing speech: {e}")
            call_log.log_route_result(
                vapi_call_id,
                transcript=transcript,
                intent="other",
                action="",
                outcome="callback",
            )
    else:
        call_log.log_route_result(
            vapi_call_id,
            transcript=transcript,
            intent="other",
            action="",
            outcome="callback",
        )
    
    # Mark as ended
    ended_at = call.get("endedAt", call.get("updatedAt"))
    call_log.call_ended(vapi_call_id, ended_at=ended_at, full_transcript=transcript)
    
    log.info(f"Synced VAPI call {call_id[:20]} to dashboard")
    return True

def sync_recent_calls(limit=20) -> dict:
    """Sync recent VAPI calls. Returns stats."""
    log.info(f"Starting VAPI sync (limit={limit})")
    
    calls = fetch_vapi_calls(limit=limit)
    
    if not calls:
        return {"synced": 0, "skipped": 0, "total": 0}
    
    synced = 0
    skipped = 0
    ended_total = 0
    
    for call in calls:
        if (call.get("status") or "").lower() == "ended":
            ended_total += 1
        if sync_call(call):
            synced += 1
        else:
            skipped += 1
    
    log.info(f"VAPI sync complete: {synced} synced, {skipped} skipped, {len(calls)} total")
    
    return {
        "synced": synced,
        "skipped": skipped,
        "total": len(calls),
        "ended_total": ended_total,
    }
