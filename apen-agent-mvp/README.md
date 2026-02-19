# APEN Agent MVP

Backend and web dashboard for the **AI conversational agent MVP** — 24/7 call reception, appointment booking, callback summaries. Aligned with the [Feasibility Study](../Feasibility-Study-AI-Conversational-Agent-APEN.md).

## MVP scope (P0)

| Capability | Description |
|------------|-------------|
| **24/7 reception** | No wait; any voice provider (Vapi, Bland, etc.) calls our API. *Vapi integration in testing.* |
| **Intent qualification** | Appointment, callback, info, emergency, after-sales, partner, other. AI when `OPENAI_API_KEY` set, else keywords. |
| **Appointment booking** | Slots from Google Calendar; create events (9h–18h Paris). |
| **Transfer rules** | Route to operations / support / commercial / reception by intent and site (`config/routing_rules.yaml`). |
| **Callback summary** | Store caller info and reason; AI extracts fields from transcript when `OPENAI_API_KEY` set. |
| **Planning & email** | `POST /planning/upload`, `GET /planning/{id}`; `POST /email/ack`, `POST /email/send` (SMTP). |

---

## Quick start

### 1. Install

```bash
cd apen-agent-mvp
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

Copy `.env.example` to `.env`. Key variables:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Whisper (audio), AI intent, callback extraction, Add to calendar (AI) |
| `GOOGLE_CALENDAR_ID` | Calendar ID (e.g. `primary` or `c_xxx@group.calendar.google.com`) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` | OAuth for calendar (when service account keys are blocked) |

Calendar: use **OAuth** on Render — run `python scripts/oauth_refresh_token.py` once, add redirect URI `http://localhost:8766/` to your OAuth client if the script uses port 8766.

### 3. Run

```bash
./run.sh
# or: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- **App:** http://localhost:8000/
- **API docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

---

## Project structure

```
apen-agent-mvp/
├── config/
│   ├── intents.yaml           # Intent keywords (FR/EN)
│   ├── routing_rules.yaml     # Transfer rules by intent and site
│   ├── voice.yaml             # Greeting, messages
│   └── scripts/               # Call scripts
├── src/
│   ├── main.py                # FastAPI app
│   ├── intent.py              # Intent detection (AI + keywords)
│   ├── ai_intent.py           # OpenAI-based intent
│   ├── ai_automation.py       # Add to calendar (AI)
│   ├── voice.py               # Voice logic (provider-agnostic)
│   ├── vapi_webhook.py        # Vapi Server URL handler
│   ├── calendar_client.py     # Google Calendar (OAuth or service account)
│   ├── summary_store.py      # Callback summaries
│   ├── call_log.py           # Call log for dashboard
│   ├── transcribe.py         # Whisper
│   ├── planning.py           # Planning upload/download
│   └── email_send.py         # SMTP
├── frontend/                  # Dashboard (EN/FR, light/dark theme)
├── scripts/
│   ├── oauth_refresh_token.py  # Get Google OAuth refresh token
│   └── test_calendar.py        # Test calendar connectivity
├── data/                      # Runtime data
├── requirements.txt
├── .env.example
├── render.yaml
└── docs/
```

---

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/config` | Base URL, webhook URL |
| POST | `/intent` | Detect intent from text `{ "message": "...", "language": "fr" }` |
| POST | `/audio/intent` | Upload audio → Whisper → intent + action + routing |
| GET | `/slots?date=YYYY-MM-DD` | Available appointment slots |
| POST | `/appointments` | Create calendar event |
| GET | `/calendar/events?days=14` | List upcoming events |
| POST | `/automation/callback-to-calendar/{id}` | Add callback to calendar (AI picks slot) |
| GET | `/calls` | Recent calls (simulated + Vapi) |
| GET | `/summaries?status=pending` | List callback summaries |
| PATCH | `/summaries/{id}` | Update status |
| GET | `/voice/prompt` | Greeting for call start |
| POST | `/voice/process` | Process transcript → intent, transfer or callback |
| POST | `/webhooks/vapi` | Vapi Server URL |
| POST | `/planning/upload` | Upload planning file |
| GET | `/planning/{id}` | Download planning |
| POST | `/email/ack` | Acknowledgment email |
| POST | `/email/send` | Send email (SMTP) |

---

## Dashboard

- **Bilingual:** EN / FR
- **Theme:** Light / dark toggle
- **Sections:** Intent & audio tests, simulated call, calls list, callbacks, calendar (events, slots, create appointment)
- **Add to calendar (AI):** One-click from callback summary → AI suggests title/description, books first free slot in 8 days

---

## Voice (Vapi)

*Vapi integration is in testing phase.*

1. Set **Server URL** in Vapi to `https://your-app/webhooks/vapi`
2. Add tools: `apen_route`, `apen_get_slots`, `apen_book_appointment`
3. Configure tools in Vapi dashboard (apen_route, apen_get_slots, apen_book_appointment)

---

## Deploy on Render

Summary:

1. Connect repo, set **Root Directory** to `apen-agent-mvp`
2. **Build:** `pip install -r requirements.txt`
3. **Start:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. **Env:** `BASE_URL`, `OPENAI_API_KEY`, `GOOGLE_CALENDAR_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
5. **Vapi:** Server URL = `https://your-app.onrender.com/webhooks/vapi`

---

## Testing

**Calendar:**
```bash
python scripts/test_calendar.py
```

**Audio intent:**
```bash
curl -X POST "http://localhost:8000/audio/intent?language=fr" -F "file=@recording.mp3"
```

---

## License

APEN internal – feasibility and MVP scope.
