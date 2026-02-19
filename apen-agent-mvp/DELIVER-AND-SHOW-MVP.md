# Delivering and showing the MVP

This is how you **deliver** the MVP (get it running) and **show** it (demo flow). No slides — you run the app and demonstrate it.

---

## 1. Deliver: get the MVP running

**One-time setup** (if not done yet):

```bash
cd apen-agent-mvp
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Every time you want to show the MVP:**

```bash
cd apen-agent-mvp
./run.sh
```

Wait until you see something like: `Uvicorn running on http://0.0.0.0:8000`

**Then open in your browser:**

| What to show | URL |
|--------------|-----|
| **MVP app (main demo)** | **http://localhost:8000/** |
| API docs (optional) | http://localhost:8000/docs |

---

## 2. Show: demo flow (what to do on screen)

Do this in order so the audience sees the full MVP.

| Step | What you do | What they see |
|------|-------------|---------------|
| **1** | Open **http://localhost:8000/** | APEN Agent MVP page; **API OK** in green = backend is up. |
| **2** | Scroll to **Test intent (texte)**. Type: `Je voudrais un rendez-vous pour récupérer ma tenue` → click **Détecter** | Result: **Intent: appointment**, **Action: book_appointment**, **Routage: in_agent** — the “brain” qualifies the request. |
| **3** | Scroll to **Test audio (Whisper + intent)**. Click **Choisir un fichier**, select your audio file (e.g. .mp3, .wav). Leave **FR** selected → click **Transcrire & intent** | File name appears; then “Transcription en cours…” then a result box: **Transcription: …** (what was said), **Intent: …**, **Action: …**, **Routage: …** — same pipeline as text, but from real speech. |
| **4** | Scroll to **Créneaux disponibles**. Pick a date → **Charger** | List of time slots (e.g. 09:00 → 09:30, …). Shows the agenda/slots API. |
| **5** | Scroll to **Créer un rendez-vous**. Fill start/end, object e.g. `Récupération tenue – David` → **Créer le RDV** | With Google Calendar configured: event created. Without: you explain “same API, calendar is plug-in”. |
| **6** | Scroll to **Rappels (callback)**. Click **Actualiser** | List of callback summaries (from previous tests or voice). Show filter (En attente / Rappelé) and “Ajouter une synthèse” to show the flow. |
| **7** | Scroll to **Voice**. Show the **Server URL** and **Copier** | Explains: “For real calls we give this URL to Vapi; our API drives the conversation, slots, transfer, and summaries.” |

**Optional:** Open **http://localhost:8000/docs** and briefly show the endpoints (e.g. `POST /intent`, `GET /slots`, `POST /webhooks/vapi`) to show it’s a real API, not a mock.

---

## 3. If something goes wrong

- **“API hors ligne” / API not responding**  
  Terminal must be running `./run.sh`. Nothing else should use port 8000.

- **Import or run error**  
  `pip install -r requirements.txt` in the same venv, then `./run.sh` again.

- **No calendar / RDV fails**  
  Expected if `.env` has no Google credentials. Say: “The booking API is in place; we plug in the calendar for the pilot.”

- **Audio test returns an error or 503**  
  The audio pipeline uses OpenAI Whisper. Add `OPENAI_API_KEY=sk-...` to `apen-agent-mvp/.env` and restart `./run.sh`. Without it, only the text intent test works.

---

## 4. What you’re actually delivering

- **A running web app** at http://localhost:8000/ that talks to your backend.
- **Intent + routing** from natural language (FR).
- **Slots API** (and optional calendar-backed booking).
- **Callback summaries** (list, add, status).
- **Voice-ready** webhook URL for Vapi (or another provider) to drive real calls.

You’re **delivering and showing the MVP** by running it and walking through this flow — no PPT required.

---

## 5. Alignment with the project subject (Feasibility Study)

This MVP is built **according to** the *Feasibility Study – AI Conversational Agent for APEN*:

| Project subject (feasibility) | In the MVP |
|------------------------------|------------|
| APEN = private security, multi-site (Paris, Le Havre, Reims, Nancy, Nantes) | Stated in hero; sites in routing and in “Rappels” (site selector). |
| Inbound calls: appointment (e.g. uniform collection), info, emergencies, partners, after-sales | Intents: **appointment** (keywords: tenue, récupérer tenue, RDV), **info**, **emergency**, **after_sales**, **partner**, **other**. |
| 24/7 reception, no wait | Voice provider (e.g. Vapi) + our API; webhook and `/voice/process`. |
| Automate appointment booking → slots + calendar | `GET /slots`, `POST /appointments`, Google Calendar. |
| Transfer to the right person after qualifying reason | `config/routing_rules.yaml` by intent and site; API returns `routing_target` / transfer number. |
| Written summary for callback | `POST /summaries`, `GET /summaries`, list/filter, status (pending / called / closed). |
| “Our stack” (transparency, all features): planning, email ack | `POST /planning/upload`, `GET /planning/{id}`; `POST /email/ack`, `POST /email/send`. |

So the demo you show **is** the MVP from the feasibility study: same scope (P0 + P1 with our stack), same use cases, same intents and routing. When asked “is it according to the project subject?”, the answer is **yes** — and the hero on the app plus this table are the evidence.
