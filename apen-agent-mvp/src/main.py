"""
APEN Agent MVP – FastAPI app.
Endpoints for intent detection, calendar slots, appointment creation, and callback summaries.
Fully config-driven; startup automates storage init and config validation.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging

# Load .env from project root (apen-agent-mvp/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
import tempfile
import os
import uuid

from . import intent, calendar_client, summary_store, call_log
from .config_loader import get_routing_rules, get_routing_target, get_intents
from . import transcribe
from . import voice
from . import planning
from . import email_send
from . import vapi_webhook
from . import ai_automation

log = logging.getLogger("apen-agent-mvp")


def _startup():
    """Automated startup: ensure storage, validate config, log env status."""
    summary_store.ensure_storage()
    planning.ensure_storage()
    call_log.ensure_storage()
    intents_data = get_intents()
    intent_ids = list((intents_data.get("intents") or {}).keys())
    routing_data = get_routing_rules()
    by_intent = (routing_data.get("routing") or {}).get("by_intent") or {}
    for iid in intent_ids:
        if (by_intent.get(iid) or {}).get("target") is None:
            log.warning("Config: intent %s has no routing target in routing_rules.yaml", iid)
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_google = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")) and os.path.exists(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""))
    has_base = bool(os.environ.get("BASE_URL"))
    log.info(
        "Startup: storage ready | OpenAI=%s | Google Calendar=%s | BASE_URL=%s",
        has_openai, has_google, has_base,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _startup()
    yield
    # shutdown if needed later


app = FastAPI(
    title="APEN Agent MVP API",
    description="Backend for AI conversational agent: intent, calendar, callback summaries.",
    version="0.1.0",
    lifespan=lifespan,
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


def _get_base_url(request: Request) -> str:
    """Base URL for links (from BASE_URL env or request headers)."""
    base = os.environ.get("BASE_URL", "").rstrip("/")
    if not base:
        try:
            scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
            host = request.headers.get("x-forwarded-host") or request.url.netloc
            base = f"{scheme}://{host}"
        except Exception:
            base = "http://localhost:8000"
    return base.rstrip("/")


@app.get("/config")
def get_config(request: Request):
    """
    Public config for the frontend (base URL for webhook, planning links).
    Set BASE_URL in production (e.g. https://your-app.onrender.com).
    """
    base = _get_base_url(request)
    return {
        "base_url": base,
        "webhook_path": "/webhooks/vapi",
        "webhook_url": f"{base}/webhooks/vapi",
    }


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


@app.get("/calendar/events")
@app.get("/calendar/events/")
def list_calendar_events(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: int = 14,
):
    """
    List upcoming calendar events. Optional from_date/to_date (YYYY-MM-DD) or days (default 14).
    Returns events with id, summary, description, start, end, htmlLink so all info is findable in the calendar.
    """
    now = datetime.utcnow()
    if from_date:
        try:
            time_min = datetime.strptime(from_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(422, "Invalid from_date, use YYYY-%m-%d")
    else:
        time_min = now
    if to_date:
        try:
            time_max = datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(422, "Invalid to_date, use YYYY-%m-%d")
    else:
        time_max = time_min + timedelta(days=min(days, 60))
    if time_max <= time_min:
        time_max = time_min + timedelta(days=days)
    events = calendar_client.list_events(time_min=time_min, time_max=time_max)
    return {
        "events": events,
        "from": time_min.strftime("%Y-%m-%d"),
        "to": time_max.strftime("%Y-%m-%d"),
        "calendar_configured": calendar_client.is_configured(),
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
    return {
        "date": dt.strftime("%Y-%m-%d"),
        "slots": slots,
        "calendar_configured": calendar_client.is_configured(),
    }


@app.options("/appointments")
@app.options("/appointments/")
def options_appointments():
    return {}

@app.post("/appointments")
@app.post("/appointments/")
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


def _designated_for_callback(site: str) -> dict:
    """Return designated person for callback (reception per site) from routing rules."""
    data = get_routing_rules()
    by_site = (data.get("routing") or {}).get("by_site") or {}
    site = site or (data.get("routing") or {}).get("default_site") or "paris"
    numbers = by_site.get(site) or by_site.get("paris") or {}
    number = numbers.get("reception") or ""
    return {"target": "reception", "label": "Reception", "number": number or ""}


@app.get("/summaries")
def list_summaries(status: Optional[str] = None, limit: int = 50):
    """List callback summaries for follow-up. Filter by status: pending, called, closed. Each summary includes designated_for_callback (transfer to)."""
    summaries = summary_store.list_summaries(status=status, limit=limit)
    for s in summaries:
        s["designated_for_callback"] = _designated_for_callback(s.get("site") or "paris")
    return {"summaries": summaries}


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


# --- AI automation (e.g. callback → calendar) ---

@app.options("/automation/callback-to-calendar/{summary_id}")
def options_automation_callback(summary_id: str):
    return {}

@app.post("/automation/callback-to-calendar/{summary_id}")
def automation_callback_to_calendar(summary_id: str):
    """
    Use AI to build a calendar event from a callback summary, then create it in the calendar.
    Picks the first available slot from tomorrow (or today). Requires OPENAI_API_KEY and calendar configured.
    """
    s = summary_store.get_summary(summary_id)
    if not s:
        raise HTTPException(404, "Summary not found")
    suggested = ai_automation.suggest_calendar_event_for_callback(s)
    if not suggested:
        raise HTTPException(503, "OPENAI_API_KEY not set. AI automation unavailable.")
    # First try tomorrow, then today
    now = datetime.utcnow()
    for days_ahead in (1, 0):
        day = (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
        slots = calendar_client.get_available_slots(day)
        if slots:
            slot = slots[0]
            ev = calendar_client.create_appointment(
                slot["start"],
                slot["end"],
                suggested["title"],
                suggested["description"],
                attendee_email=None,
            )
            if ev and ev.get("id"):
                return {
                    "ok": True,
                    "summary_id": summary_id,
                    "event": ev,
                    "message": f"Calendar event created: {suggested['title']}",
                }
    raise HTTPException(503, "No free slot found (today or tomorrow). Calendar may be full or not configured.")


# --- Call log (Vapi calls → dashboard) ---

def _call_purpose_line(c: dict) -> str:
    """One-line purpose summary from intent, outcome, transcript, and scheduling."""
    events = c.get("events") or []
    last = events[-1] if events else {}
    intent = (last.get("intent") or "").strip() or "inquiry"
    outcome = (last.get("outcome") or "").strip()
    transcript = (last.get("transcript") or "").strip()[:80]
    if transcript and len((last.get("transcript") or "")) > 80:
        transcript = transcript.rstrip() + "…"
    reason = (c.get("summary_reason") or "").strip()[:60]
    if reason and len((c.get("summary_reason") or "")) > 60:
        reason = reason.rstrip() + "…"
    appointment_id = c.get("appointment_id")
    # Build purpose line by intent
    intent_labels = {
        "appointment": "Appointment request",
        "callback": "Callback request",
        "info": "Information request",
        "emergency": "Urgent / emergency",
        "after_sales": "After-sales",
        "partner": "Partner inquiry",
        "other": "Other",
    }
    label = intent_labels.get(intent, intent.replace("_", " ").title()) if intent else "Other"
    if appointment_id:
        return f"{label} — appointment booked."
    if outcome == "transfer":
        return f"{label} — transferred to team."
    if reason:
        return f"{label} — {reason}"
    if transcript and transcript != "—":
        return f"{label} — {transcript}"
    return f"{label} — callback noted."


@app.get("/calls")
def list_calls(limit: int = 100):
    """List recent calls (transcript, intent, outcome, importance, scheduling, purpose). Enriched with summary and one-line purpose."""
    calls = call_log.list_calls(limit=limit)
    for c in calls:
        sid = c.get("summary_id")
        if sid:
            s = summary_store.get_summary(sid)
            if s:
                c["importance"] = s.get("urgency") or "—"
                c["summary_reason"] = (s.get("reason") or "")[:200]
        if not c.get("importance"):
            c["importance"] = "—"
        c["scheduling"] = "Appointment booked" if c.get("appointment_id") else "—"
        c["purpose"] = _call_purpose_line(c)
    return {"calls": calls}


# --- Voice (provider-agnostic: Vapi, Bland, or any platform – no Twilio) ---

class VoiceProcessRequest(BaseModel):
    transcript: str
    caller_phone: str = ""
    site: Optional[str] = None
    language: str = "fr"


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
    For test calls (e.g. from the dashboard tester), also logs a synthetic call and runs post-call automation:
    call appears in Calls with ended_at and full_transcript; callback summary notes get the transcript.
    """
    call_id = "test-" + str(uuid.uuid4())[:8]
    call_log.log_call_started(call_id, body.caller_phone or "")
    result = voice.process_speech(body.transcript, body.caller_phone, body.site, body.language)
    outcome = "transfer" if result.get("response_type") == "transfer" else "callback"
    # When test call is appointment intent, try to actually book a slot so the user sees an appointment created
    if result.get("intent") == "appointment" and result.get("action") == "book_appointment":
        tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        slots = calendar_client.get_available_slots(tomorrow)
        if slots:
            slot = slots[0]
            subject = "Uniform collection (test call)"
            desc_parts = ["APEN – Prise de rendez-vous (agent IA)"]
            if (body.transcript or "").strip():
                desc_parts.append("Reason: " + (body.transcript or "").strip()[:300])
            if (body.caller_phone or "").strip():
                desc_parts.append("Caller: " + (body.caller_phone or "").strip())
            desc_parts.append("Designated: Reception (callback/transfer)")
            ev = calendar_client.create_appointment(
                slot["start"], slot["end"], subject, "\n".join(desc_parts), attendee_email=None
            )
            if ev and ev.get("id"):
                result["appointment_id"] = ev["id"]
                result["response_type"] = "appointment_booked"
                result["say_message"] = f"Rendez-vous confirmé: {subject} le {slot['start'][:10]} à {slot['start'][11:16]}."
                outcome = "appointment_booked"
                call_log.log_appointment_booked(call_id, ev["id"])
    call_log.log_route_result(
        call_id,
        transcript=(body.transcript or "").strip(),
        intent=result.get("intent") or "other",
        action=result.get("action") or "",
        outcome=outcome,
        summary_id=result.get("summary_id"),
        appointment_id=result.get("appointment_id"),
    )
    call_log.call_ended(call_id, full_transcript=(body.transcript or "").strip())
    c = call_log.get_call(call_id)
    if c and c.get("summary_id") and (body.transcript or "").strip():
        summary_store.update_notes(c["summary_id"], (body.transcript or "").strip(), append=True)
    result["call_id"] = call_id
    return result


# --- Vapi webhook (build Limova and more: our brain + Vapi for the phone) ---

def _webhook_vapi_get():
    return {"message": "APEN webhook OK. Use POST for assistant-request, tool-calls, transfer-destination-request."}


def _webhook_vapi_post(body: dict):
    response = vapi_webhook.handle_vapi_message(body)
    if response is not None:
        return response
    return {}


@app.get("/webhooks/vapi")
@app.get("/webhooks/vapi/")
def webhook_vapi_get():
    """GET so you can verify the URL is reachable (e.g. in browser)."""
    return _webhook_vapi_get()


@app.options("/webhooks/vapi")
@app.options("/webhooks/vapi/")
def webhook_vapi_options():
    """CORS preflight."""
    return {}


@app.post("/webhooks/vapi")
@app.post("/webhooks/vapi/")
def webhook_vapi_post(body: dict):
    """
    Vapi Server URL. Handles assistant-request (our greeting + tools),
    tool-calls (apen_route, apen_get_slots, apen_book_appointment), transfer-destination-request (return number).
    Set in Vapi: Server URL = https://your-app.com/webhooks/vapi (no trailing slash recommended).
    """
    return _webhook_vapi_post(body)


# --- Planning (publish/send – beyond Limova) ---

@app.post("/planning/upload")
def planning_upload(request: Request, file: UploadFile = File(...)):
    """Upload a planning file (PDF, Excel, etc.). Returns id and link to download."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in planning.ALLOWED_EXTENSIONS:
        raise HTTPException(422, f"Unsupported format. Allowed: {', '.join(planning.ALLOWED_EXTENSIONS)}")
    content = file.file.read()
    try:
        result = planning.save_planning(content, file.filename or "planning")
    except ValueError as e:
        raise HTTPException(422, str(e))
    base = _get_base_url(request)
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
