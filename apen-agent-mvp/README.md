# APEN Agent MVP

Backend and configuration for the **AI conversational agent MVP** (inbound calls, appointment booking, callback summaries). Aligned with the [Feasibility Study](../Feasibility-Study-AI-Conversational-Agent-APEN.md).

## MVP scope (P0)

- **24/7 reception** – no wait (any **voice provider** – Vapi, Bland, etc. – calls our API; **no Twilio**)
- **Intent qualification** – appointment, info, emergency, after-sales, partner, other
- **Appointment booking** – slots from Google Calendar, create events (e.g. uniform collection)
- **Transfer rules** – route to operations / support / commercial / reception by intent and site
- **Callback summary** – store caller info and reason for follow-up (auto from voice flow)
- **Planning publish/send** – upload file, get download link (POST `/planning/upload`, GET `/planning/{id}`)
- **Email auto-reply** – personalized acknowledgment (POST `/email/ack`); send email (POST `/email/send`) with SMTP

**We build Limova and more:** [docs/WE-BUILD-LIMOVA-AND-MORE.md](docs/WE-BUILD-LIMOVA-AND-MORE.md). Use **Vapi** with our **POST /webhooks/vapi** as Server URL for full voice flow (no Twilio, no Limova). See also [docs/Beyond-Limova.md](docs/Beyond-Limova.md).

## Pipeline (structure)

1. **Input** – Text (POST `/intent`) or audio (POST `/audio/intent` → Whisper → text).
2. **Config** – `config/intents.yaml` (keywords, action per intent) and `config/routing_rules.yaml` (routing target per intent).
3. **Intent + action + routing** – Backend returns `intent`, `action`, `routing_target` for every message.
4. **Downstream** – According to action: use **slots + appointments** (book_appointment), **transfer** (by intent/site), or **summaries** (collect_summary for callback).

Full flow and module roles: [docs/PIPELINE.md](docs/PIPELINE.md).

## Project structure

```
apen-agent-mvp/
├── config/
│   ├── intents.yaml           # Intent definitions and keywords
│   ├── routing_rules.yaml     # Transfer rules by intent and site
│   └── scripts/               # Call scripts (greeting, appointment, transfer, summary)
├── src/
│   ├── main.py                # FastAPI app + frontend routes
│   ├── config_loader.py       # Load YAML + get_routing_target()
│   ├── intent.py              # Rule-based intent detection
│   ├── transcribe.py          # Whisper API (audio → text)
│   ├── voice.py               # Voice logic (provider-agnostic: Vapi, Bland, etc. – no Twilio)
│   ├── planning.py            # Planning upload/store/download
│   ├── email_send.py          # SMTP + acknowledgment template
│   ├── calendar_client.py     # Google Calendar integration
│   └── summary_store.py       # Callback summary storage (JSON file)
├── frontend/                  # Web UI (index.html, styles.css, app.js)
├── data/                      # Runtime: callback_summaries.json, plannings/
├── requirements.txt
├── .env.example
├── README.md
└── docs/
    └── pilot-checklist.md
```

## Quick start

### 1. Install dependencies

```bash
cd apen-agent-mvp
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Environment (optional for calendar)

Copy `.env.example` to `.env` and set:

- `GOOGLE_APPLICATION_CREDENTIALS` – path to Google service account JSON
- `GOOGLE_CALENDAR_ID` – calendar ID (e.g. `primary` or the shared calendar ID)

- `OPENAI_API_KEY` – for **audio testing**: transcribe with Whisper and get intent (POST `/audio/intent`).

If not set, the API will still run; **GET /slots** returns generic slots and **POST /appointments** returns 503 until calendar is configured. **POST /audio/intent** returns 503 until `OPENAI_API_KEY` is set.

### 3. Run the API

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- **App (frontend):** http://localhost:8000/ or http://localhost:8000/app/  
- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  
- Config (base URL, webhook URL): http://localhost:8000/config  

## Deploy on Render

See **[RENDER.md](RENDER.md)** for step-by-step instructions.

Summary:

1. **New Web Service** → connect repo, set **Root Directory** to `apen-agent-mvp`.
2. **Build:** `pip install -r requirements.txt`
3. **Start:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. **Environment:** Set `BASE_URL` (your app URL), `OPENAI_API_KEY`, `GOOGLE_CALENDAR_ID`. For **calendar on Render** use **OAuth** (no service account key): set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` — get the refresh token locally with `python scripts/oauth_refresh_token.py` (see [RENDER.md](RENDER.md)).
5. **Vapi:** Server URL = `https://your-app.onrender.com/webhooks/vapi`.

A `render.yaml` is in this directory for Blueprint deploy.

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/config` | Base URL and webhook URL (for frontend; uses `BASE_URL` or request) |
| POST | `/intent` | Detect intent from text `{ "message": "...", "language": "fr" }` |
| POST | `/audio/intent` | **Upload audio file** → transcribe (Whisper) → intent + action + routing (needs `OPENAI_API_KEY`) |
| GET | `/slots?date=2025-02-18` | Available appointment slots for a date |
| POST | `/appointments` | Create calendar event (body: start_iso, end_iso, summary, …) |
| GET | `/routing` | Get routing rules (for agent config) |
| POST | `/summaries` | Store callback summary |
| GET | `/summaries?status=pending` | List summaries (pending / called / closed) |
| GET | `/summaries/{id}` | Get one summary |
| PATCH | `/summaries/{id}` | Update status `{ "status": "called" }` |
| GET | `/voice/prompt` | Greeting text for start of call (any provider uses for TTS) |
| POST | `/voice/process` | **Provider-agnostic:** body `{ transcript, caller_phone }` → intent, transfer_number or say_message |
| POST | `/webhooks/vapi` | **Vapi Server URL** – we return assistant + apen_route tool; handle transfer-destination-request (build Limova and more) |
| POST | `/planning/upload` | Upload planning file → id + download_url |
| GET | `/planning/{id}` | Download planning file |
| POST | `/email/ack` | Generate/send acknowledgment (incoming_subject, incoming_from, to?) |
| POST | `/email/send` | Send email (to, subject, body) – needs SMTP env |

## Testing with an audio file

1. Set `OPENAI_API_KEY` in `.env` (or export it).
2. Install deps and start the API (see Quick start).
3. Call the audio endpoint:

```bash
curl -X POST "http://localhost:8000/audio/intent?language=fr" \
  -F "file=@/path/to/your/audio.mp3"
```

Response: `transcript`, `intent`, `action`, `routing_target`. You can also use the **Swagger UI** at http://localhost:8000/docs → **POST /audio/intent** → Try it out → choose your file.

Supported formats: **mp3, wav, m4a, webm, ogg, flac**.

## Voice (provider-agnostic – no Twilio)

1. **Any voice platform** (Vapi, Bland, or your SIP/STT) handles the phone number and the call.
2. **GET /voice/prompt** – Get greeting text; use it for your TTS.
3. **POST /voice/process** – Send `{ "transcript": "...", "caller_phone": "+33..." }`; we return `response_type` (transfer | callback), `transfer_number` or `say_message`, and we create a callback summary when not transferring.
4. **Transfer numbers** – Edit `config/routing_rules.yaml` and replace `+33XXXXXXXX` with real numbers per site. See [docs/Beyond-Limova.md](docs/Beyond-Limova.md).

## Delivering and showing the MVP

To **run and demo** the MVP (no slides): [DELIVER-AND-SHOW-MVP.md](DELIVER-AND-SHOW-MVP.md) — start the app, open http://localhost:8000/, follow the step-by-step demo flow.

## Pilot runbook

See [docs/pilot-checklist.md](docs/pilot-checklist.md) for PoC/Pilot steps, KPIs and go-live checklist.

## License / internal use

APEN internal – feasibility and MVP only.
