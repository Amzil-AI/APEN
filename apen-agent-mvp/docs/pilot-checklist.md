# APEN Agent MVP – Pilot checklist

Use this checklist for the **Proof of Concept** and **Pilot** phases (see [Feasibility Study](../Feasibility-Study-AI-Conversational-Agent-APEN.md)).

---

## Pre-PoC (before starting)

- [ ] Feasibility study validated internally (management, operations, IT)
- [ ] Pilot site or pilot phone line chosen (e.g. one agency)
- [ ] Business referent assigned (operations / reception)
- [ ] IT referent assigned (calendar, API, Limova if used)
- [ ] Limova (or other vendor) contacted: demo, quote, DPA

---

## PoC setup (4–6 weeks)

### Configuration

- [ ] Call scripts updated in `config/scripts/` for your wording and cases
- [ ] `config/intents.yaml` – keywords adjusted to real caller phrases
- [ ] `config/routing_rules.yaml` – transfer numbers filled per site
- [ ] Google Calendar: service account created, calendar shared, `GOOGLE_CALENDAR_ID` and credentials set
- [ ] API running and tested: `/health`, `/intent`, `/slots`, `/appointments`, `/summaries`

### Scenarios to validate

- [ ] **Reception** – Greeting and intent detection (appointment / info / emergency / other)
- [ ] **Appointment** – Slot proposal and event creation in calendar (e.g. uniform collection)
- [ ] **Transfer** – Correct transfer to operations / support / commercial for test intents
- [ ] **Summary** – Callback summary created and visible in GET `/summaries`

### Integration (if using Limova)

- [ ] Tom configured with greeting and options matching scripts
- [ ] Tom → webhook to this API for appointment creation and/or summary (if supported)
- [ ] Or: use Tom’s native Google Agenda + manual process for summaries during Pilot

---

## Pilot (6–8 weeks)

- [ ] Go-live on pilot line with clear start date
- [ ] Team trained: how to read summaries, how to handle transfers, how to check calendar
- [ ] Callers informed (e.g. “You may be speaking to an AI assistant” if required)
- [ ] KPIs tracked:
  - [ ] Number of calls handled by agent vs transferred
  - [ ] Number of appointments created via agent
  - [ ] Callback summary count and time-to-callback
  - [ ] Satisfaction or feedback (survey or sample)
- [ ] Weekly review of misrouted calls and script adjustments

---

## Go / No-go for rollout

- [ ] KPIs acceptable (e.g. >X% resolution without transfer for simple cases, no critical misrouting)
- [ ] No blocking issues (calendar sync, transfer failures, compliance)
- [ ] Decision: extend to all sites and/or add phase 2 (planning, email)

---

*Reference: Standard AI project management workflow – Feasibility → PoC → Pilot → Production.*
