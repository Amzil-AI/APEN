# We Build Limova and More

APEN Agent is **our own** conversational voice and automation stack. We deliver what Limova does—and more—without depending on Limova as a vendor.

---

## What we build

| Capability | Limova | We build |
|------------|--------|----------|
| **Inbound calls, 24/7, no wait** | ✅ | ✅ **Vapi** (or any provider) + our API |
| **Speech on the call (STT + TTS)** | ✅ | ✅ Handled by **Vapi**; logic is ours |
| **Intent from what the caller said** | ✅ | ✅ **Our config** (intents.yaml, routing_rules.yaml) |
| **Appointment booking + calendar** | ✅ | ✅ **Our API** (slots, appointments, Google Calendar) |
| **Transfer to the right person** | ✅ | ✅ **Our routing** → we tell Vapi the number |
| **Callback summary (synthèse pour rappel)** | ✅ | ✅ **Our API** (summaries, auto from voice flow) |
| **Send/publish planning** | ❌ | ✅ **Our API** (planning upload, download link) |
| **Email auto-reply (acknowledgment)** | ❌ | ✅ **Our API** (email/ack, email/send) |

So we **build the Limova layer** (voice agent with intent, routing, calendar, summaries) and **add** planning and email.

---

## How it works end-to-end

1. **Phone number and call** – Use **Vapi** (or another provider): buy a number, set **Server URL** to our app.
2. **Our brain** – When a call comes in, Vapi sends **assistant-request** to `POST /webhooks/vapi`. We return an assistant that:
   - Says **our greeting** (from `GET /voice/prompt`).
   - Has one tool: **apen_route(user_message, caller_phone)**. When the user speaks, Vapi calls that tool; we run **our** intent + routing and return `transfer_number` or `say_message`.
3. **Transfer** – If we return a `transfer_number`, the assistant can request a transfer; Vapi sends **transfer-destination-request** and we return that number (we stored it for the call).
4. **Callback** – If we don’t transfer, we return `say_message` (“Un conseiller vous rappellera”) and **we already created a callback summary** in our system (Rappels in the dashboard).
5. **Planning & email** – Your team uses our app: upload planning (link to share or send by email), trigger acknowledgments or send emails via our API.

All routing, intents, calendar, summaries, planning, and email logic live in **our codebase**; Vapi (or another provider) is only the “phone + STT + TTS” layer.

---

## Setup: “Limova and more” in production

1. **Deploy our API** – Run the app (e.g. `uvicorn src.main:app`) behind HTTPS. Example: `https://agent.apen.fr`.
2. **Vapi** – Create a Vapi account, add a phone number, set **Server URL** to `https://agent.apen.fr/webhooks/vapi`. No need to create an assistant in the UI; we return it from the webhook.
3. **Config** – Edit `config/routing_rules.yaml`: replace `+33XXXXXXXX` with real transfer numbers per site.
4. **Optional** – Google Calendar (for slots/RDV), SMTP (for email), BASE_URL (for planning links).

After that, calls to your Vapi number are answered by **our** greeting and **our** routing; we create callback summaries and we can do planning and email beyond what Limova offers.

---

## Summary

- **We build** the product: intents, routing, calendar, summaries, planning, email.
- **We use** a voice provider (e.g. Vapi) only for the call and speech; no Twilio, no Limova dependency.
- **Result:** our own “Limova and more” stack, under our control.
