# APEN Agent MVP – Pipeline & architecture

## MVP pipeline (step-by-step)

The flow is: **take call → get what they said → check intent → act** (book RDV, transfer, or collect summary).

| Step | What happens | In the MVP |
|------|----------------|------------|
| **1. Take call** | Inbound call arrives (Vapi or other voice provider). | Provider answers 24/7; no queue. |
| **2. Greet** | Agent says the opening phrase. | `GET /voice/prompt` → greeting (e.g. “Bonjour, vous êtes en contact avec APEN…”). |
| **3. Get what they said** | Caller speaks (e.g. “Je voudrais un rendez-vous pour récupérer ma tenue”). Provider turns speech → text (STT). | Transcript sent to our API (e.g. `POST /voice/process` or Vapi tool `apen_route` with `user_message`). |
| **4. Check intent** | We classify the message: appointment, info, emergency, after_sales, partner, other. | `intent.detect_intent(transcript, "fr")` + `config/intents.yaml` (keywords). |
| **5. Decide action** | From intent we get: book_appointment, provide_info, transfer, or collect_summary. | `intent.get_intent_action(intent_id)` + `config_loader.get_routing_target(intent_id)`. |
| **6. Act** | **If appointment:** propose slots, create event in calendar. **If transfer:** dial the right number (operations / support / commercial). **If callback:** store summary for later call-back. | **Book:** `GET /slots`, `POST /appointments` (Google Calendar). **Transfer:** return `transfer_number` → provider dials. **Callback:** `POST /summaries` (nom, tél, motif, site). |

So: **Take call → Greet → Get speech (transcript) → Check intent → Decide action → Act** (book / transfer / summary). The demo (text intent, audio intent, slots, RDV, rappels, voice URL) exercises this same pipeline.

---

## Data flow (high level)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ENTRANTS (Voice / Text)                                                     │
│  • Appel entrant → Limova Tom (ou autre) → transcription                     │
│  • Ou: enregistrement audio uploadé → Whisper (POST /audio/intent)          │
│  • Ou: texte saisi → POST /intent                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONFIG (YAML)                                                               │
│  config/intents.yaml     → mots-clés FR/EN par intention                     │
│  config/routing_rules.yaml → cible de routage par intention (+ par site)     │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  INTENT + ACTION + ROUTING                                                   │
│  src/intent.py           → detect_intent(message, lang) → intent_id         │
│                           → get_intent_action(intent_id) → action            │
│  src/config_loader.py    → get_routing_target(intent_id) → target           │
│  Réponse API: { intent, action, routing_target }                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            ▼                           ▼                           ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│ action =          │     │ action =          │     │ action =           │
│ book_appointment  │     │ transfer          │     │ collect_summary    │
│ routing = in_agent│     │ routing =         │     │ routing = reception│
└─────────┬─────────┘     │ operations/       │     └─────────┬─────────┘
          │               │ support/commercial│               │
          ▼               └─────────┬─────────┘               ▼
┌───────────────────┐               │               ┌───────────────────┐
│ GET /slots        │               │               │ POST /summaries   │
│ POST /appointments│               ▼               │ (nom, tél, motif, │
│ (Google Calendar) │     Transfert téléphonique    │  site, urgence)   │
└───────────────────┘     vers numéro du site      └───────────────────┘
```

## Intents → Actions → Routing (single source of truth)

| Intent       | Action           | Routing target | Usage |
|-------------|------------------|----------------|--------|
| appointment | book_appointment | in_agent       | Proposer créneaux, créer RDV (agenda) |
| info        | provide_info     | in_agent       | Donner horaires, adresse, infos |
| emergency   | transfer         | operations     | Transférer vers opérations |
| after_sales | transfer         | support        | Transférer vers SAV |
| partner     | transfer         | commercial     | Transférer vers commercial |
| other       | collect_summary  | reception      | Noter synthèse pour rappel |

Defined in: `config/intents.yaml` (keywords + action) and `config/routing_rules.yaml` (by_intent.target).

## Backend modules

| Module            | Role |
|-------------------|------|
| `config_loader.py`| Charge intents.yaml, routing_rules.yaml ; expose get_intents(), get_routing_rules(), get_routing_target() |
| `intent.py`       | detect_intent(text, lang), get_intent_action(intent_id) à partir des config |
| `transcribe.py`   | transcribe_audio(path, lang) via OpenAI Whisper API |
| `calendar_client.py` | get_available_slots(date), create_appointment(...) via Google Calendar API |
| `summary_store.py`   | add_summary(...), list_summaries(), get_summary(), update_status() ; persistance JSON |
| `main.py`         | FastAPI : routes, app frontend, appels aux modules ci-dessus |

## Frontend → API

- **Intent (texte):** `POST /intent` → affiche intent, action, routing_target.
- **Audio:** `POST /audio/intent` → affiche transcript, intent, action, routing_target.
- **Créneaux:** `GET /slots?date=YYYY-MM-DD` → affiche liste de créneaux.
- **Créer RDV:** `POST /appointments` (start_iso, end_iso, summary, …).
- **Rappels:** `GET /summaries`, `POST /summaries`, `PATCH /summaries/{id}` (status).

Toutes les réponses d’intent (texte ou audio) ont la même forme : `intent`, `action`, `routing_target`.

## Checklist cohérence

- [ ] Chaque intent dans `intents.yaml` a une entrée dans `routing_rules.yaml` → `by_intent.<intent>.target`.
- [ ] Les actions (book_appointment, provide_info, transfer, collect_summary) correspondent aux cas d’usage (RDV, info, transfert, rappel).
- [ ] Les numéros de transfert par site dans `routing_rules.yaml` sont renseignés pour la prod.
