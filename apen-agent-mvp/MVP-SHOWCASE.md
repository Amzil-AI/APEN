# APEN Agent MVP — Product Showcase

**AI conversational agent for 24/7 call reception across Paris, Le Havre, Reims, Nancy and Nantes.**

---

## Executive summary

The APEN Agent MVP is a reception system that handles inbound calls 24/7 with no waiting. It qualifies each call, books appointments, transfers to the right team, or creates callback summaries — all driven by your rules and connected to your calendar. Voice integration (e.g. Vapi) is in testing phase; the API and dashboard are production-ready for intent, callbacks, and calendar.

Built according to the Feasibility Study, the MVP delivers transparency: all logic lives in your codebase and config, not in a vendor black box. You own the data and can audit every decision.

---

## What it does

| Capability | Description |
|------------|-------------|
| **24/7 reception** | Calls are answered immediately, anytime. No queue, no “please hold”. *(Voice/Vapi integration in testing.)* |
| **Appointment booking** | Callers can book slots (e.g. uniform collection). The agent proposes available times (9h–18h Paris, max 10 slots/day) and creates the event in Google Calendar automatically. |
| **Call qualification** | Detects intent from what the caller says: appointment, callback, info, emergency, after-sales, partner, or other. Uses AI when `OPENAI_API_KEY` is set, else keyword-based. |
| **Smart transfers** | Emergency → operations. After-sales → support. Partners → commercial. Rules are configurable per intent and per site in `config/routing_rules.yaml`. |
| **Callback summaries** | For callback/other requests, the agent collects name, phone, reason and site, and saves a summary for your team to call back. AI extracts fields from transcript when `OPENAI_API_KEY` is set. |
| **Planning & email** | API only (no dashboard UI): `POST /planning/upload`, `GET /planning/{id}`; `POST /email/ack`, `POST /email/send`. Requires SMTP env for sending. |

---

## End‑to‑end workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. INBOUND CALL                                                         │
│     Caller dials your number → Voice provider (e.g. Vapi) answers 24/7   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. GREETING                                                            │
│     “Bonjour, vous êtes en contact avec APEN. Dites le motif…”          │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. SPEECH → TEXT                                                        │
│     Caller speaks → transcribed to text (STT) → sent to our API         │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. INTENT DETECTION                                                    │
│     AI (or keywords) classify: appointment | callback | info | emergency│
│     | after-sales | partner | other                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ APPOINTMENT     │    │ TRANSFER        │    │ CALLBACK         │
│ Offer slots     │    │ Dial the right   │    │ Save summary:    │
│ from Calendar   │    │ number (ops /    │    │ name, phone,    │
│ → Create event  │    │ support /        │    │ reason, site     │
│                 │    │ commercial)      │    │ for later call   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Intent → action mapping

| Intent | What happens | Routing |
|--------|--------------|----------|
| **Appointment** | Offer slots, book in calendar | Stays with agent (`in_agent`) |
| **Callback** | Collect summary (name, phone, reason) for call back | Reception |
| **Info** | Provide information (hours, address) | Stays with agent (`in_agent`) |
| **Emergency** | Transfer to operations | Operations number |
| **After-sales** | Transfer to support | Support number |
| **Partner** | Transfer to commercial | Commercial number |
| **Other** | Collect summary for call back (unclassified) | Reception |

Rules and transfer numbers are configurable per site (Paris, Le Havre, Reims, Nancy, Nantes) in `config/routing_rules.yaml`.

---

## Dashboard (web interface)

The MVP includes a web dashboard to manage calls, callbacks, and appointments.

### 1. Intent & audio tests

- **Text:** Type a phrase (“Je voudrais un rendez-vous pour récupérer ma tenue”) → see intent, action, routing.
- **Audio:** Upload a recording → transcribe (Whisper) → same pipeline. Useful for testing real speech.

### 2. Simulated call

- Enter what the caller said (or upload a recording).
- Add caller phone (optional).
- Click **Simulate call** → runs full flow: intent → callback summary or appointment. When intent is **appointment**, the system automatically books the first available slot for tomorrow and creates the calendar event. Call appears in **Calls** with transcript and outcome.

### 3. Live calls (Vapi)

- Connect Vapi to the webhook URL shown in the dashboard (`https://your-app/webhooks/vapi`).
- Real calls use the same API: greet, qualify, book, transfer, or callback. Test number is shown in the dashboard (e.g. +1 661 480 9377).
- *Vapi is currently in testing phase; live calls are for validation and demos.*

### 4. Calls list

- Recent calls (simulated tests and live Vapi calls): transcript, intent, action, outcome, importance, scheduling.
- See which calls led to an appointment or a callback.

### 5. Callbacks

- List of requests pending callback.
- Filter by status: Pending | Called back | Closed.
- For each: name, phone, reason, site, urgency.
- **Add to calendar (AI):** One click → AI suggests title and description → creates a calendar event for the first free slot in the next 8 days (today through 7 days ahead). Requires `OPENAI_API_KEY`.
- Update status: Called back, Close.

### 6. Calendar

- **Upcoming events:** Next 14 days (from start of today Paris time), with links to open in Google Calendar.
- **Available slots:** Pick a date → load up to 10 slots (9h–18h Paris, 30‑min intervals, excluding busy times).
- **Create appointment:** Manual form for start, end, subject, description, optional attendee email.

---

## AI automation

Requires `OPENAI_API_KEY` in the environment.

- **Intent detection:** AI (gpt-4o-mini) first when key is set, keyword fallback otherwise — more accurate for varied phrasing.
- **Callback summary:** AI extracts `caller_name`, `reason`, `urgency`, `site` from transcript for new summaries.
- **Add to calendar (AI):** From a callback summary, AI proposes title and description; system finds the first free slot in the next 8 days (Paris timezone) and creates the event. If no key, returns 503.

---

## Voice integration (Vapi)

**Note:** Vapi integration is still in testing phase. Live call handling and phone routing are under validation; use for demos and PoC until fully validated.

1. Create an assistant in the Vapi dashboard.
2. Set **Server URL** to `https://your-app.onrender.com/webhooks/vapi`.
3. Add three tools: `apen_route`, `apen_get_slots`, `apen_book_appointment`.
4. Attach the assistant to your phone number.
5. Calls use our API for routing, slots, and booking.

See [VAPI-ASSISTANT-SETUP.md](VAPI-ASSISTANT-SETUP.md) for step-by-step configuration.

---

## Deployment

The MVP runs on [Render](https://render.com) (or similar):

- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- **Environment:** `BASE_URL`, `OPENAI_API_KEY`, `GOOGLE_CALENDAR_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` (OAuth). Optional: `VAPI_ASSISTANT_ID`, `SMTP_*` for email.

Calendar on Render uses **OAuth** (no service account JSON). Run `python scripts/oauth_refresh_token.py` once to get the refresh token; add the redirect URI (`http://localhost:8766/` if the script uses port 8766) to your OAuth client in Google Cloud. See [RENDER.md](RENDER.md).

---

## Bilingual support

The dashboard supports **English** and **French**. Use the language selector in the header to switch. Intent detection and audio tests support FR and EN input.

---

## Technology stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Intent | AI (OpenAI) + keyword config |
| Calendar | Google Calendar API (OAuth or service account) |
| Voice | Provider-agnostic (Vapi, Bland, etc.) |
| Frontend | Vanilla JS, i18n (EN/FR) |
| Deployment | Render (or any Python host) |

---

## Alignment with Feasibility Study

| Study requirement | MVP |
|-------------------|-----|
| 24/7 reception, no wait | ✅ Via voice provider + our API (Vapi in testing) |
| Appointment booking + calendar | ✅ Slots + Google Calendar |
| Transfer after qualification | ✅ Configurable per intent and site |
| Callback summary | ✅ Auto from voice, list, status, Add to calendar |
| Multi-site (Paris, Le Havre, Reims, Nancy, Nantes) | ✅ Sites in config and UI |
| Transparency | ✅ All logic in our repo and config |
| Planning, email | ✅ Upload/planning API, email ack/send |

---

## Next steps

- **Proof of Concept:** Deploy and test with one site or one number.
- **Pilot:** Limited rollout, KPIs, user feedback.
- **Production:** Broader deployment after validation.

See [docs/pilot-checklist.md](docs/pilot-checklist.md) for pilot steps and go-live checklist.

---

*APEN Agent MVP — internal use, feasibility and pilot scope.*
