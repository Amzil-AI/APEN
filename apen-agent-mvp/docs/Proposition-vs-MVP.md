# Your Proposals vs MVP – Coverage

*Reference: follow-up to the phone conversation – intelligent conversational agent for APEN.*

---

## Your 5 proposals – status in the MVP

| # | Your proposal | In MVP? | Details |
|---|----------------|--------|---------|
| **1** | **AI agent – inbound call handling, replace current voice server** | **Partially** | The MVP provides the **logic** (intent, routing, slots, summaries) and an **API + test UI**. **Actual call handling** and **multiple simultaneous calls** require an **external voice agent** (e.g. Limova Tom) that would call our API. Without Limova (or similar), there is no live phone traffic through the agent. |
| **2** | **Appointment booking and automatic entry in a calendar (e.g. uniform collection for David)** | **Yes** | Intent `appointment` with keywords “rendez-vous”, “tenue”, “récupérer tenue”; **GET /slots**; **POST /appointments** (Google Calendar); frontend form. The “uniform collection” use case is covered. |
| **3** | **Sending or publishing a schedule/planning** | **No** | Planned for **phase 2** (post-MVP) in the feasibility study. Not implemented in the MVP. |
| **4** | **Automatic reply to certain emails (personalised acknowledgments)** | **No** | Also **phase 2**. Not in the MVP. |
| **5** | **Summary for callback (draft and send)** | **Yes** | Intent `other` → action `collect_summary`; **POST /summaries** (caller name, phone, reason, site, urgency); **GET /summaries**; frontend “Rappels” to add, list, and mark as called or closed. |
| **6** | **Intelligent transfer to the right person after analysing the reason for contact** | **Yes** | Analysing the reason = **intents** (appointment, info, emergency, after-sales, partner, other); **routing_target** per intent (in_agent, operations, support, commercial, reception); **config/routing_rules.yaml** with numbers per site. The **actual phone transfer** would be done by Limova (or the switchboard) using our API/rules. |

---

## Summary

- **In the MVP:**  
  - Appointment booking and automatic calendar entry (including uniform collection).  
  - Callback summary (create, list, update status).  
  - Analysing the reason for contact and **deciding** who to transfer to.

- **Requires Limova (or another voice agent):**  
  - Real inbound calls and multiple simultaneous calls; performing the actual transfer on the phone system.

- **Planned for phase 2 (not in MVP):**  
  - Sending/publishing planning.  
  - Automatic email replies (acknowledgments).
