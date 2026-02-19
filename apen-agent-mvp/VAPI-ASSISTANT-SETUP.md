# Vapi assistant setup (full routing + booking)

Two ways to get the call working **and** keep routing/booking (apen_route, slots, book appointment).

---

## Option A: Create assistant in Vapi (recommended)

You create one assistant in the Vapi dashboard, set its **Server URL** to your app, add the 3 tools, then attach that assistant to your phone number. No env var needed.

### 1. Create the assistant

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai) → **Assistants** → **Create Assistant**.
2. **Name:** e.g. `APEN Reception`.
3. **First message:** e.g.  
   `Bonjour, vous êtes en contact avec APEN. Dites brièvement le motif de votre appel : rendez-vous, information, urgence, ou autre.`
4. **Model:** e.g. OpenAI → `gpt-4o-mini` (or your choice).
5. **System prompt:** paste this (or adapt):

   ```
   You are APEN's voice agent.
   1) When the user states their reason for calling, call the apen_route tool with their message and caller_phone.
   2) If the result says intent is "appointment" and action is "book_appointment": call apen_get_slots (with date if they gave one), tell the user the available slots, ask which one they want; when they choose, call apen_book_appointment with that slot's start_iso, end_iso, and subject (e.g. Uniform collection).
   3) If the result has transfer_number, use the transferCall tool to transfer and say the say_message.
   4) If only say_message is set (callback), say it to the user and end the call.
   Be brief and professional. Language: French.
   ```

6. **Voice:** e.g. 11labs → choose a voice (e.g. Rachel or your preferred one).

### 2. Set the Server URL (assistant or phone number)

You need your webhook URL in one of these places so Vapi can send **tool-calls** to your app.

**Option 2a – On the assistant (if you see it)**  
1. Open your assistant and look for one of these tabs/sections: **Advanced**, **Server**, **Webhooks**, or **Integration**.  
2. In that section, find **Server URL** (or **Webhook URL** / **Server URL**).  
3. Set it to:  
   `https://YOUR-APP-URL/webhooks/vapi`  
   (e.g. `https://your-app.onrender.com/webhooks/vapi` — no trailing slash).  
4. Save.

**Option 2b – On the phone number (if you don’t see Server URL on the assistant)**  
1. Go to **Phone Numbers** → click your number.  
2. Find **Server URL** (or **Webhook** / **Server**).  
3. Set it to the same URL:  
   `https://YOUR-APP-URL/webhooks/vapi`  
4. Save.  

When this number is used, tool-calls will go to that URL. You still attach the assistant to this number in step 4 below.

### 3. Add the three tools

In the assistant, go to the **Tools** tab (not "Functions" — use **Tools**). Add these three as **server/custom** or **function** tools. Each uses the assistant’s Server URL (no need to set a URL per tool if the assistant URL is set).

**Tool 1 – apen_route**

- **Name:** `apen_route`
- **Description:** `Get routing for the caller. Call with the user's message and caller phone. Returns transfer_number or say_message. Use first to qualify the call.`
- **Parameters (JSON Schema):**

```json
{
  "type": "object",
  "properties": {
    "user_message": { "type": "string", "description": "What the caller said" },
    "caller_phone": { "type": "string", "description": "Caller phone number" }
  },
  "required": ["user_message"]
}
```

**Tool 2 – apen_get_slots**

- **Name:** `apen_get_slots`
- **Description:** `Get available appointment slots for a date. Call when the caller wants to book. date format YYYY-MM-DD.`
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "date": { "type": "string", "description": "Date for slots, YYYY-MM-DD. Omit for tomorrow." }
  }
}
```

**Tool 3 – apen_book_appointment**

- **Name:** `apen_book_appointment`
- **Description:** `Book an appointment. Call after the caller chose a slot. start_iso and end_iso must match a slot from apen_get_slots.`
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "start_iso": { "type": "string", "description": "Slot start ISO, e.g. 2026-02-20T10:00:00" },
    "end_iso": { "type": "string", "description": "Slot end ISO, e.g. 2026-02-20T10:30:00" },
    "subject": { "type": "string", "description": "Appointment subject, e.g. Uniform collection" },
    "email": { "type": "string", "description": "Caller email if given (optional)" }
  },
  "required": ["start_iso", "end_iso", "subject"]
}
```

Save the assistant.

### 4. Attach the assistant to your phone number (required)

1. Go to **Phone Numbers** → click your number.
2. Look for **Inbound** or **Inbound settings** (the assistant and Server URL for incoming calls are often there).
3. Set **Assistant** to the assistant you just created (APEN Reception).  
   **You must set an assistant here.** If the number has a Server URL but no assistant, Vapi will send an "assistant-request" to your server; if that fails or times out, you’ll see: *"Couldn't get assistance? Either set the assistant ID on the phone number or …"*
4. Keep **Server URL** on the number (or on the assistant) so tool-calls reach your app.

When someone calls, Vapi uses this assistant and sends **tool-calls** to your Server URL (`/webhooks/vapi`). The API will handle apen_route, apen_get_slots, and apen_book_appointment.

**Dashboard tip:** If the UI says "Tools" (not "Functions"), use the **Tools** tab and add each of the three as a **tool** with the name and parameters below. Our webhook accepts the same payload either way.

---

## Option B: Dynamic assistant (return assistant ID from your app)

Use this if you want the **phone number** to have no assistant and your app to decide which assistant to use (e.g. by number or time).

1. Create the assistant in Vapi as in Option A (Server URL + 3 tools). Save and copy the **Assistant ID**.
2. In your app env set (APEN assistant ID):  
   `VAPI_ASSISTANT_ID=6e7ec3f7-9f71-432c-bb27-ff039d01c9b4`
3. In Vapi: **Phone Numbers** → your number → leave **Assistant** empty and set **Server URL** to  
   `https://YOUR-APP-URL/webhooks/vapi`.

On each call, Vapi sends **assistant-request** to your URL; your app responds with `{"assistantId": "asst_xxxx"}` and Vapi uses that assistant. Tool-calls still go to the same webhook.

---

## Quick checklist

- [ ] Assistant created with first message, model, system prompt, voice.
- [ ] **Server URL** set (on the assistant under **Advanced** / **Server** / **Webhooks**, or on the **Phone Number**) = `https://YOUR-APP-URL/webhooks/vapi`.
- [ ] Three **tools** added (in the **Tools** tab): `apen_route`, `apen_get_slots`, `apen_book_appointment` (names and parameters as above).
- [ ] Phone number has this assistant selected (Option A) or Server URL set + `VAPI_ASSISTANT_ID` in app (Option B).
- [ ] App is deployed and reachable at that URL; `OPENAI_API_KEY` set if the model needs it.

If the call drops as soon as it connects, see the README / troubleshooting: use a **minimal** assistant (no inline tools) or this pre-created assistant setup.

---

## "Couldn't get assistance?" error

If you see: *"Couldn't get assistance? Either set the assistant ID on the phone number or to debug your assistant request, Check the debugging artifacts that were just sent to your server."*

- **Fix:** On the **Phone Numbers** page, open your number and go to **Inbound** (or **Inbound settings**). Set **Assistant** to your APEN assistant. Do not leave the assistant empty when using a Server URL for tool-calls.
- **Why:** When the number has no assistant, Vapi asks your server for one (assistant-request). If the server doesn’t respond in time or returns something invalid, Vapi shows this message. Setting the assistant on the number avoids that request.
- **To debug:** In Vapi’s call or webhook logs, check the “debugging artifacts” to see the request sent to your server and the response. On your server (e.g. Render logs), look for `Vapi assistant-request received` or errors when the webhook is called.

---

## Post-call automation (after the call ends)

When a call ends, the app can automatically:

- Mark the call with **ended_at** and store the **full transcript** (if Vapi sends it).
- Append the full transcript to the linked **callback summary** notes so advisors see the full conversation.

To enable this, Vapi must send **end-of-call-report** (and optionally **status-update** when status is `ended`) to your Server URL.

1. In the Vapi dashboard, open your **Assistant** (or the one used by your number).
2. Find **Advanced** / **Server** / **Webhooks** or **Server Messages** (or similar).
3. Enable **End of Call Report** and, if available, **Status Updates**.
4. Ensure the assistant (or phone number) **Server URL** is set to `https://YOUR-APP-URL/webhooks/vapi`.

The webhook accepts:

- `message.type` = `end-of-call-report` (or `endOfCallReport`) — full transcript is extracted and stored; the linked callback summary notes are updated.
- `message.type` = `status-update` with `message.status` = `ended` — call is marked as ended; transcript is stored if present in the payload.

After that, the Calls dashboard shows **ended_at** and **full_transcript** for each call, and the Pipeline (callback summaries) shows the full conversation in the summary notes.

---

## AI intent and callback summary

When **OPENAI_API_KEY** is set, the app uses **OpenAI (gpt-4o-mini)** for:

- **Intent detection** – The caller’s message is classified into one of: appointment, callback, info, emergency, after_sales, partner, other. If the API is unavailable or errors, the app falls back to keyword-based detection from `config/intents.yaml`.
- **Callback summary** – When a callback is created (no transfer), the transcript is analysed to extract: **caller name** (if mentioned), **short reason**, **urgency** (low/medium/high), and **site** (e.g. paris). These fields are stored in the callback summary; if the API is unavailable, the app uses defaults (e.g. “Appelant”, full transcript slice, medium, paris).

So live calls (Vapi), simulated test calls, and **POST /voice/process** all benefit from AI intent and AI-extracted summaries when the key is set.

---

## AI automation (callback → calendar)

The app can create a **calendar event** from a callback summary using AI:

- **Endpoint:** `POST /automation/callback-to-calendar/{summary_id}`
- **Behaviour:** Loads the callback summary, uses OpenAI (same `OPENAI_API_KEY` as Whisper) to suggest a title and description (e.g. “Rappel – Jean Dupont”, with caller, phone, reason, site, “Designated: Reception”), then books the **first available slot** for today or tomorrow and creates the event in Google Calendar.
- **Requirements:** `OPENAI_API_KEY` set; Google Calendar configured (`GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CALENDAR_ID`).
- **Frontend:** In **Callbacks**, each summary has an **“Add to calendar (AI)”** button that calls this endpoint and refreshes the Calendar list on success.
