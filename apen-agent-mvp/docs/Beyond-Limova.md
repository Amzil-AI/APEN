# APEN Agent – Beyond Limova (Competitor Differentiation)

We build **our own** logic and automation so we are not dependent on Limova or any single vendor. **We do not use Twilio.** Any voice provider (Vapi, Bland, SIP gateway, etc.) can plug into our API.

---

## 1. Voice layer (provider-agnostic – no Twilio)

| Feature | Limova Tom | Our stack |
|--------|------------|-----------|
| Intent from speech | ✅ | ✅ **POST /voice/process** with transcript + caller_phone |
| Transfer to right person | ✅ | ✅ We return `transfer_number`; your provider does the dial |
| Callback summary | ✅ | ✅ We create it automatically when not transferring |
| Greeting / prompt | ✅ | ✅ **GET /voice/prompt** returns text for your TTS |

**How it works**

- Your **voice platform** (Vapi, Bland, or any SIP/telephony with STT) handles the phone number and the call.
- At call start: **GET /voice/prompt** → use the returned text for your TTS greeting.
- After the caller speaks: **POST /voice/process** with `{ "transcript": "...", "caller_phone": "+33..." }` → we return:
  - `response_type`: `"transfer"` or `"callback"`
  - `transfer_number`: number to dial (if transfer)
  - `say_message`: text to speak (if callback)
  - plus `intent`, `action`, `routing_target`
- Your platform then either transfers to `transfer_number` or says `say_message` and hangs up. We create a callback summary when `response_type` is `"callback"`.

**No Twilio.** Use Vapi, Bland, or any provider that can do STT and call our JSON API.

---

## 2. Planning (send/publish)

| Feature | Limova | Our stack |
|--------|--------|-----------|
| Send or publish a schedule/planning | ❌ | ✅ **POST /planning/upload** + **GET /planning/{id}** |

- **POST /planning/upload**: upload a file (PDF, Excel, etc.) → we store it and return an id and **download_url**.
- **GET /planning/{id}**: download the file (e.g. share link or send by email via **POST /email/send**).

So we cover “envoi ou publication d’un planning” in-house.

---

## 3. Email auto-reply (acknowledgments)

| Feature | Limova | Our stack |
|--------|--------|-----------|
| Personalized acknowledgment emails | ❌ (other product) | ✅ **POST /email/ack** (+ optional SMTP send) |

- **POST /email/ack**: body = `incoming_subject`, `incoming_from`, optional `to`.
  - We return (and optionally send) a **personalized acknowledgment** text.
  - If `to` is set and SMTP is configured, we send the email; otherwise we only return `reply_subject` and `reply_body`.

Configure **SMTP_*** and **EMAIL_FROM** in env to actually send; otherwise the endpoint still generates the reply for you to send elsewhere.

---

## 4. Single stack, no vendor lock-in

- **Intent, routing, calendar, summaries**: same logic for voice (Twilio), for the test UI, and for any future channel (e.g. WhatsApp, another telephony provider).
- **Config-driven**: all behaviour from **config/intents.yaml** and **config/routing_rules.yaml**; we own the data and the rules.
- **Extensible**: add new intents, new actions, new channels without depending on Limova’s roadmap.

---

## Summary

| Your requirement | Limova | Our build |
|------------------|--------|-----------|
| Agent IA, appels entrants | ✅ | ✅ Twilio + /voice/* |
| RDV + agenda | ✅ | ✅ /slots, /appointments |
| Synthèse pour rappel | ✅ | ✅ /summaries + auto from voice |
| Transfert intelligent | ✅ | ✅ TwiML Dial + routing_rules |
| Envoi/publication planning | ❌ | ✅ /planning/upload, /planning/{id} |
| Réponse auto e-mail (accusé) | ❌ | ✅ /email/ack, /email/send |

We do **more** than Limova (planning, email ack) and **build the full flow** with **Vapi**: set your Vapi Server URL to **POST /webhooks/vapi** and we become the brain (assistant + apen_route tool + transfer destination). No Twilio. See [WE-BUILD-LIMOVA-AND-MORE.md](WE-BUILD-LIMOVA-AND-MORE.md).
