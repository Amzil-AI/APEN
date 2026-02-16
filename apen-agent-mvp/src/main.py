"""
APEN Agent MVP – FastAPI app.
Endpoints for intent detection, calendar slots, appointment creation, and callback summaries.
Can be used by Limova webhooks or by a custom frontend/CLI for the PoC.
"""
from pathlib import Path
from datetime import datetime
from typing import Optional

# Load .env from project root (apen-agent-mvp/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
import tempfile
import os

from . import intent, calendar_client, summary_store
from .config_loader import get_routing_rules, get_routing_target
from . import transcribe
from . import voice
from . import planning
from . import email_send
from . import vapi_webhook

app = FastAPI(
    title="APEN Agent MVP API",
    description="Backend for AI conversational agent: intent, calendar, callback summaries.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response models ---

class IntentRequest(BaseModel):
    message: str
    language: str = "fr"


class AppointmentCreate(BaseModel):
    start_iso: str = Field(..., description="Start datetime ISO format")
    end_iso: str = Field(..., description="End datetime ISO format")
    summary: str = Field(..., description="Title of the appointment")
    description: str = ""
    attendee_email: Optional[str] = None


class SummaryCreate(BaseModel):
    caller_name: str
    caller_phone: str
    reason: str
    site: str = "paris"
    urgency: str = "medium"
    callback_preference: Optional[str] = None
    notes: Optional[str] = None
    call_id: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|called|closed)$")


# --- Routes ---

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
def root():
    """Redirect to frontend app."""
    return RedirectResponse(url="/app/", status_code=302)


@app.get("/app/")
def app_index():
    """Serve frontend index.html."""
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "Frontend not found")
    return FileResponse(index, media_type="text/html")


@app.get("/app")
def app_redirect():
    return RedirectResponse(url="/app/", status_code=302)


@app.get("/app/{path:path}")
def app_static(path: str):
    """Serve frontend: index.html for empty path, else static files (CSS, JS)."""
    if ".." in path or path.startswith("/"):
        raise HTTPException(404, "Not found")
    if not path or path.endswith("/"):
        file_path = FRONTEND_DIR / "index.html"
    else:
        file_path = FRONTEND_DIR / path
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "Not found")
    media_types = {".css": "text/css", ".js": "application/javascript", ".html": "text/html"}
    media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")
    return FileResponse(file_path, media_type=media_type)


@app.get("/health")
def health():
    return {"status": "ok", "service": "apen-agent-mvp"}


@app.post("/intent", response_model=dict)
def detect_intent_endpoint(body: IntentRequest):
    """Detect intent from a text message (e.g. transcribed from voice)."""
    intent_id = intent.detect_intent(body.message, body.language)
    action = intent.get_intent_action(intent_id)
    routing_target = get_routing_target(intent_id)
    return {"intent": intent_id, "action": action, "routing_target": routing_target}


# --- Audio testing ---

@app.post("/audio/intent", response_model=dict)
async def audio_to_intent(
    file: UploadFile = File(..., description="Audio file (mp3, wav, m4a, webm, etc.)"),
    language: str = "fr",
):
    """
    Upload an audio file: transcribe with Whisper, then detect intent and action.
    Requires OPENAI_API_KEY. Use for testing call flows with real voice samples.
    """
    ext = (file.filename or "audio.mp3").lower().split(".")[-1]
    if ext not in ("mp3", "wav", "m4a", "webm", "ogg", "flac", "mp4", "mpeg"):
        raise HTTPException(
            422,
            "Unsupported format. Use mp3, wav, m4a, webm, ogg, flac.",
        )
    suffix = os.path.splitext(file.filename or "audio.mp3")[1] or ".mp3"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            transcript = transcribe.transcribe_audio(tmp_path, language=language if language in ("fr", "en") else None)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    except ValueError as e:
        raise HTTPException(503, str(e))

    if not transcript:
        return {
            "transcript": "",
            "intent": "other",
            "action": "collect_summary",
            "routing_target": "reception",
            "message": "No speech detected in audio.",
        }

    intent_id = intent.detect_intent(transcript, language)
    action = intent.get_intent_action(intent_id)
    routing_target = get_routing_target(intent_id)

    return {
        "transcript": transcript,
        "intent": intent_id,
        "action": action,
        "routing_target": routing_target,
    }


@app.get("/slots")
def get_slots(date: Optional[str] = None):
    """
    Get available appointment slots for a date.
    date: YYYY-MM-DD (default: today).
    """
    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(422, "Invalid date, use YYYY-MM-DD")
    else:
        dt = datetime.now()
    slots = calendar_client.get_available_slots(dt)
    return {"date": dt.strftime("%Y-%m-%d"), "slots": slots}


@app.post("/appointments")
def create_appointment_endpoint(body: AppointmentCreate):
    """Create a calendar appointment (e.g. uniform collection)."""
    result = calendar_client.create_appointment(
        start_iso=body.start_iso,
        end_iso=body.end_iso,
        summary=body.summary,
        description=body.description,
        attendee_email=body.attendee_email,
    )
    if result is None:
        raise HTTPException(503, "Calendar not configured or insert failed. Set GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CALENDAR_ID.")
    return result


@app.get("/routing")
def get_routing():
    """Return routing rules (for agent or Limova config)."""
    return get_routing_rules()


# --- Callback summaries ---

@app.post("/summaries", response_model=dict)
def create_summary(body: SummaryCreate):
    """Store a callback summary (e.g. from Limova webhook or agent)."""
    return summary_store.add_summary(
        caller_name=body.caller_name,
        caller_phone=body.caller_phone,
        reason=body.reason,
        site=body.site,
        urgency=body.urgency,
        callback_preference=body.callback_preference,
        notes=body.notes,
        call_id=body.call_id,
    )


@app.get("/summaries")
def list_summaries(status: Optional[str] = None, limit: int = 50):
    """List callback summaries for follow-up. Filter by status: pending, called, closed."""
    return {"summaries": summary_store.list_summaries(status=status, limit=limit)}


@app.get("/summaries/{summary_id}")
def get_summary(summary_id: str):
    s = summary_store.get_summary(summary_id)
    if not s:
        raise HTTPException(404, "Summary not found")
    return s


@app.patch("/summaries/{summary_id}")
def update_summary_status(summary_id: str, body: StatusUpdate):
    """Mark summary as called or closed."""
    s = summary_store.update_status(summary_id, body.status)
    if not s:
        raise HTTPException(404, "Summary not found")
    return s


# --- Voice (provider-agnostic: Vapi, Bland, or any platform – no Twilio) ---

class VoiceProcessRequest(BaseModel):
    transcript: str
    caller_phone: str = ""
    site: Optional[str] = None


@app.get("/voice/prompt")
def voice_prompt():
    """Greeting text for the start of a call (any provider uses this for TTS)."""
    return {"prompt": voice.get_greeting_text()}


@app.post("/voice/process")
def voice_process(body: VoiceProcessRequest):
    """
    Process caller speech. Any voice platform (Vapi, Bland, SIP, etc.) POSTs transcript + caller_phone.
    Returns: intent, action, routing_target, response_type (transfer | callback),
    transfer_number (if transfer), say_message (if callback). Creates callback summary when not transferring.
    """
    return voice.process_speech(body.transcript, body.caller_phone, body.site)


# --- Vapi webhook (build Limova and more: our brain + Vapi for the phone) ---

@app.post("/webhooks/vapi")
def webhook_vapi(body: dict):
    """
    Vapi Server URL. Handles assistant-request (our greeting + apen_route tool),
    tool-calls (apen_route → our routing), transfer-destination-request (return number).
    Set in Vapi: Server URL = https://your-app.com/webhooks/vapi
    """
    response = vapi_webhook.handle_vapi_message(body)
    if response is not None:
        return response
    return {}


# --- Planning (publish/send – beyond Limova) ---

@app.post("/planning/upload")
def planning_upload(file: UploadFile = File(...)):
    """Upload a planning file (PDF, Excel, etc.). Returns id and link to download."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in planning.ALLOWED_EXTENSIONS:
        raise HTTPException(422, f"Unsupported format. Allowed: {', '.join(planning.ALLOWED_EXTENSIONS)}")
    content = file.file.read()
    try:
        result = planning.save_planning(content, file.filename or "planning")
    except ValueError as e:
        raise HTTPException(422, str(e))
    base = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
    result["download_url"] = f"{base}/planning/{result['id']}"
    return result


@app.get("/planning/{plan_id}")
def planning_download(plan_id: str):
    """Download a planning file by id."""
    path = planning.get_planning_path(plan_id)
    if not path:
        raise HTTPException(404, "Planning not found")
    return FileResponse(path, media_type="application/octet-stream", filename=path.name)


# --- Email (auto-reply / acknowledgment – beyond Limova) ---

class EmailAckRequest(BaseModel):
    incoming_subject: str = ""
    incoming_from: str = ""
    to: Optional[str] = None  # if set, send the email; else return reply body only


@app.post("/email/ack")
def email_acknowledgment(body: EmailAckRequest):
    """Generate and optionally send a personalized acknowledgment email."""
    reply_subject = "Re: " + (body.incoming_subject or "Votre message")[:60]
    reply_body = email_send.make_acknowledgment_body(body.incoming_subject, body.incoming_from)
    if body.to and email_send.can_send():
        ok = email_send.send_email(body.to, reply_subject, reply_body)
        return {"sent": ok, "reply_subject": reply_subject, "reply_body": reply_body}
    return {"sent": False, "reply_subject": reply_subject, "reply_body": reply_body}


class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str


@app.post("/email/send")
def email_send_endpoint(body: EmailSendRequest):
    """Send an email (e.g. planning link or custom message). Requires SMTP env."""
    if not email_send.can_send():
        raise HTTPException(503, "SMTP not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD.")
    ok = email_send.send_email(body.to, body.subject, body.body)
    if not ok:
        raise HTTPException(503, "Send failed.")
    return {"sent": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
