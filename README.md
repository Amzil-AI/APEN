# APEN Agent MVP

AI conversational agent for 24/7 call reception — appointment booking, callback summaries, smart transfers. Backend + web dashboard.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Quick commands and common tasks |
| **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** | Complete deployment guide |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Step-by-step checklist |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System architecture & data flow |
| **[RAILWAY_SETUP_COMPLETE.md](RAILWAY_SETUP_COMPLETE.md)** | Setup confirmation |

## 🚀 Quick Start

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for fast setup and common commands.

### Local Development
```bash
make setup    # Set up environment
make run      # Start server
```

Visit `http://localhost:8000` for the dashboard.

### Railway Deployment (Recommended)
Railway deployment is fully configured and ready to go:

```bash
# 1. Push to GitHub
# 2. Go to railway.app → New Project → Deploy from GitHub
# 3. Select this repo
# 4. Add environment variables
# 5. Done!
```

**See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for complete guide.**  
**See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for step-by-step checklist.**

## Features

- **24/7 reception** — No wait; voice provider (Vapi, Bland, etc.) calls our API *(Vapi in testing)*
- **Intent qualification** — Appointment, callback, info, emergency, after-sales, partner, other (AI or keyword-based)
- **Appointment booking** — Slots from Google Calendar, 9h–18h Paris, create events
- **Smart transfers** — Route by intent and site (operations, support, commercial, reception)
- **Callback summaries** — Store caller info; AI extracts fields when `OPENAI_API_KEY` set
- **Planning & email** — Upload planning files; send acknowledgments (API, SMTP)

## Quick start

```bash
cd apen-agent-mvp
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit .env with your keys
./run.sh
```

Open http://localhost:8000/ — dashboard (EN/FR, light/dark theme).

## Environment

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Whisper, AI intent, callback extraction, Add to calendar (AI) |
| `GOOGLE_CALENDAR_ID` | Calendar ID (e.g. `primary` or `c_xxx@group.calendar.google.com`) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` | OAuth for calendar (no service account key needed) |

**Calendar OAuth:** Run `python scripts/oauth_refresh_token.py`, add `http://localhost:8766/` to OAuth redirect URIs in Google Cloud, paste the refresh token into `.env`.

## API (main endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/intent` | Detect intent from text |
| POST | `/audio/intent` | Upload audio → Whisper → intent |
| GET | `/slots?date=YYYY-MM-DD` | Available slots |
| POST | `/appointments` | Create calendar event |
| GET | `/calendar/events` | Upcoming events |
| POST | `/automation/callback-to-calendar/{id}` | Add callback to calendar (AI) |
| GET | `/calls` | Recent calls |
| GET/PATCH | `/summaries` | List/update callbacks |
| GET | `/voice/prompt` | Greeting text |
| POST | `/voice/process` | Process transcript |
| POST | `/webhooks/vapi` | Vapi Server URL |

## Dashboard

- **Intent & audio tests** — Text or file → intent, action, routing
- **Simulated call** — Full flow; appointment auto-booked when intent is appointment
- **Calls** — Transcript, intent, outcome
- **Callbacks** — Pending/called/closed; Add to calendar (AI)
- **Calendar** — Events, slots, create appointment

## Deploy

### Railway (Recommended)

Railway deployment is fully automated with the included configuration files.

1. **Quick Deploy**: 
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select this repository
   - Railway auto-detects Python and uses `railway.toml`

2. **Set Environment Variables** in Railway dashboard:
   ```
   BASE_URL=https://your-app.railway.app
   OPENAI_API_KEY=sk-...
   GOOGLE_CALENDAR_ID=primary
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REFRESH_TOKEN=...
   ```

3. **Configure Vapi**: Server URL = `https://your-app.railway.app/webhooks/vapi`

**See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed guide.**

### Render (Alternative)

1. Connect repo, **Root Directory** = `apen-agent-mvp`
2. **Build:** `pip install -r requirements.txt`
3. **Start:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. **Env:** `BASE_URL`, `OPENAI_API_KEY`, `GOOGLE_CALENDAR_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
5. **Vapi:** Server URL = `https://your-app.onrender.com/webhooks/vapi`

## Voice (Vapi)

Set Server URL to `https://your-app/webhooks/vapi`. Add tools: `apen_route`, `apen_get_slots`, `apen_book_appointment`. *Integration in testing phase.*

## Project structure

```
config/          intents.yaml, routing_rules.yaml, voice.yaml
src/             main.py, intent.py, ai_intent.py, ai_automation.py,
                 voice.py, vapi_webhook.py, calendar_client.py,
                 summary_store.py, call_log.py, transcribe.py,
                 planning.py, email_send.py
frontend/        index.html, app.js, styles.css, i18n.js
scripts/         oauth_refresh_token.py, test_calendar.py
```

## Testing

```bash
python scripts/test_calendar.py
curl -X POST "http://localhost:8000/audio/intent?language=fr" -F "file=@recording.mp3"
```

---

APEN internal — feasibility and MVP scope.
