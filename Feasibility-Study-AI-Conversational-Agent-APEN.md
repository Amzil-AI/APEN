# Feasibility Study – AI Conversational Agent for APEN

---

## 1. Context, Objectives and Strategic Alignment

### 1.1 APEN Context

APEN is a private security company with multiple sites (Paris/Montrouge, Le Havre, Reims, Nancy, Nantes). Inbound calls cover: appointment booking (e.g. uniform collection for David), information requests, operational emergencies, partners, and after-sales. The current voice server limits responsiveness and does not allow handling multiple calls without wait times or automating simple actions (calendar, scheduling, summaries, targeted transfers).

### 1.2 Project Objectives

| Business objective | Target indicator (MVP) |
|--------------------|------------------------|
| Reduce wait time and missed calls | Immediate 24/7 response; no queue for calls handled by the agent |
| Automate appointment booking | Slots proposed and written automatically into a calendar (e.g. Google Calendar) |
| Improve call routing | Transfer to the right person after qualifying the reason for the call |
| Free up team time | Handle simple requests (hours, info, scheduling) and summaries for callback |
| Cover email and scheduling | Personalized acknowledgments; send/publish schedules within defined scope |

### 1.3 Alignment with Standard AI Framework (integration workflow)

The project follows the **Feasibility → Proof of Concept → Pilot → Production** cycle:

- **Feasibility (this study):** cost, viability, MVP scope, risks, preliminary plan.
- **Proof of Concept:** technical and functional validation in a limited environment (one site or one pilot number).
- **Pilot:** limited deployment in time and scope, user feedback collection and KPI measurement.
- **Production:** stable, scalable rollout across all sites/numbers.

---

## 2. Technological Assessment and Proposed Solution (Limova Tom, Vapi, Bland AI, Retell, etc.)

### 2.1 APEN Requirements vs Limova Tom Offer

| APEN need | Tom (Limova) | Fit |
|-----------|--------------|-----|
| 24/7 call reception, multiple simultaneous calls | 24/7 reception, no queue | ✅ Aligned |
| Appointment booking + calendar entry | Google Calendar integration, slot suggestion | ✅ Aligned |
| Intelligent transfer after analysing reason | Qualification + transfer to the right person | ✅ Aligned |
| Summary for callback | Instant report on platform | ✅ Aligned |
| Send/publish scheduling | Not natively covered by Tom | ⚠️ To address via custom or other agent/API |
| Automatic reply to certain emails | Not covered by Tom (voice) | ⚠️ Mickael (customer relations) or email integration to be specified |

**Technological conclusion:** Limova Tom covers the core need (calls, appointments, qualification, transfer, summary). “Scheduling” and “email” are either scope extensions (additional Limova agents, API) or left out of an MVP limited to phone + calendar.

### 2.2 Maturity and Integration

- **Maturity:** French commercial solution, in production (e.g. real estate agency testimonials). Voice AI technology is mature for reception and qualification.
- **Integration:** Google Calendar documented. Connection to APEN ecosystem (calendar, CRM, business tools) to be validated in PoC (APIs, connectors, SSO if needed).
- **Scalability:** Cloud architecture; scaling to multiple lines/sites to be confirmed with Limova (multi-site / multi-number offering).

### 2.3 Alternatives (to keep in mind for PoC phase)

- Other voice AI agent platforms to compare cost, integrations and GDPR: e.g. **Vapi**, **Bland AI**, **Retell**, **ElevenLabs Conversational AI**, or French/EU alternatives.
- **Own stack (in-house build):** Section 2.4 describes an approach where we own the logic (intents, routing, calendar, summaries, planning, email). Voice is handled by a provider (e.g. Vapi); we are not locked into Limova. This option is feasible and delivers transparency and full feature set from the start.

### 2.4 Why our approach: transparency and feature completeness (vs Limova, Vapi, Bland AI, Retell, etc.)

**Transparency, not black box.**  
Third‑party agents (Limova Tom, generic voice bots) typically run intent and routing inside their platform: you configure via their UI, but the rules and data live on their side. You cannot easily audit *why* a call was routed somewhere, change the logic without going through the vendor, or guarantee that only your rules are applied. Our approach is the opposite: **all decision logic is in our codebase and in versioned config (e.g. intents, routing rules)**. Every behaviour is explainable, auditable and changeable by APEN. No opaque “AI black box”; full control and traceability for compliance (GDPR, sector) and for tuning.

**One stack, all features in one place.**  
The table below compares capabilities in a single view. “APEN (our build)” is our own stack (API + config + optional voice provider e.g. Vapi); “Limova Tom” and “Other tools” (e.g. **Vapi**, **Bland AI**, **Retell**) are representative of market offerings. Features present only in our build are marked so you can discuss the project with a clear, fact-based comparison.

| Capability | APEN (our build) | Limova Tom | Other tools (e.g. Vapi, Bland AI, Retell) |
|------------|-------------------|------------|------------------------|
| **Transparency / explainability** | ✅ Full: config + code we own; every routing decision traceable | ⚠️ Platform logic; limited visibility into “why” | ⚠️ Often black box; rules and data on vendor side |
| **Intent + routing logic** | ✅ In our repo (intents, routing rules); editable, versioned | ✅ In platform (their UI/config) | ✅ In platform |
| **24/7 reception, no wait** | ✅ Via voice provider (e.g. Vapi) + our API | ✅ | ✅ |
| **Appointment booking + calendar** | ✅ Our API (slots, create event); Google Calendar | ✅ | ✅ / ⚠️ Varies |
| **Intelligent transfer** | ✅ Our routing returns number; provider dials | ✅ | ✅ |
| **Callback summary (synthèse rappel)** | ✅ Our API; auto-created from voice flow; we store it | ✅ On their platform | ⚠️ Often separate or extra |
| **Send/publish planning** | ✅ Our API (upload, download link, optional email) | ❌ Not in Tom | ❌ Rare in one product |
| **Email auto-reply (accusés de réception)** | ✅ Our API (generate/send) | ❌ Other agent (e.g. Mickael); not in Tom | ❌ Often separate |
| **Vendor lock-in** | ✅ None for logic; we choose voice carrier | ⚠️ Tied to Limova for behaviour and data | ⚠️ Tied to vendor |
| **Data location and rules** | ✅ Our infra and config; we decide retention and rules | ⚠️ Their infra; DPA and terms apply | ⚠️ Their infra |

**Takeaway for project discussions:** we target **transparency (no black box)** and **all required features in one place**. What others do not offer (planning, email ack, full control and explainability) is available in our build; what they do offer (reception, RDV, transfer, summary) we match with logic we own and can audit.

---

## 3. MVP Scope and Preliminary Plan

### 3.1 MVP Principles

- **Goal:** Validate business value and acceptance (users and callers) with a minimal scope deliverable quickly.
- **Target scope:** One site or one pilot line; priority use cases = reception + qualification + appointment booking + transfer + summary.

### 3.2 Functional MVP Scope (recommended)

| Priority | Functionality | In MVP | Comment |
|----------|---------------|--------|---------|
| P0 | 24/7 reception, no wait | Yes | Replace voice server on pilot line |
| P0 | Call reason qualification (appointment, info, emergency, after-sales, partner) | Yes | Rules and scripts to be defined with teams |
| P0 | Appointment booking and calendar entry | Yes | e.g. uniform collection – one shared calendar (Google or other) |
| P0 | Transfer to the right person / department | Yes | Routing rules by reason and site |
| P0 | Written summary for callback (report) | Yes | On Limova platform or export to internal tool |
| P1 | Send or publish scheduling | No (post-MVP) for Limova-only path | With our stack (2.4): already available |
| P1 | Automatic email replies (acknowledgments) | No (post-MVP) for Limova-only path | With our stack (2.4): already available |

**Classic MVP (e.g. Limova only) = P0 only**, on **one line / one site**. With our own stack (Section 2.4), P0 and P1 can be delivered in one product from the start.

### 3.3 Deliverables and Preliminary Milestones (aligned with Standard AI)

| Phase | Indicative duration | Main deliverables |
|-------|----------------------|-------------------|
| **Feasibility** | 2–3 weeks | This study; management validation; vendor choice (Limova, Vapi, Bland AI, Retell, or other); budget and schedule estimates |
| **Proof of Concept** | 4–6 weeks | Tom (Limova) or other agent (e.g. Vapi, Bland AI, Retell) setup on pilot line; calendar integration; scenarios: reception, appointment, transfer, summary; technical and UX validation |
| **Pilot** | 6–8 weeks | Pilot production rollout; user training; feedback collection; KPI measurement (resolution rate without transfer, satisfaction, number of appointments booked) |
| **Deployment decision** | — | Go / No-go for rollout to all sites and extension (scheduling, email) |

End-to-end estimate until rollout decision: **about 3–4 months** (subject to team and Limova availability).

### 3.4 MVP Plan (execution)

| Phase | Duration | Activities | Outputs / decision gate |
|-------|----------|------------|--------------------------|
| **Feasibility** | Weeks 1–2 | Finalise this study; internal validation (management, ops, IT); choose vendor (Limova vs our stack); rough budget and schedule | Signed-off feasibility; vendor choice; go/no-go for PoC |
| **PoC setup** | Weeks 3–4 | Provision pilot line/number; configure agent (Limova Tom or our API + Vapi); connect calendar; load intents and routing rules; define scripts and transfer numbers | Agent live on pilot line; test calendar; first test calls |
| **PoC validation** | Weeks 5–6 | Run scenarios (reception, RDV, transfer, summary); collect technical and UX feedback; fix config and rules; optional: planning + email if our stack | PoC report; validated scenarios; go/no-go for Pilot |
| **Pilot** | Weeks 7–14 | Rollout on pilot line; train users; monitor KPIs (resolution without transfer, appointments booked, satisfaction); adjust scripts and routing | Pilot report; KPI dashboard; go/no-go for Production |
| **Production (post-MVP)** | From Week 15 | Rollout to other sites/lines; extend to scheduling and email if not already in scope | Full deployment; phase 2 features as needed |

**Dependencies:** Business referent available for scenarios and validation; IT referent for calendar and APIs; pilot site/line and routing numbers defined before PoC.

---

## 4. Data, Skills, Risks and Compliance

### 4.1 Data and Voice

- **Data used:** Call recordings, transcriptions, metadata (duration, reason, transfer). With **Limova**, that data is processed on their side; hosting location and DPAs must be verified. With **our own stack** (2.4), we store only what we need (e.g. callback summaries, config); the voice provider (e.g. Vapi) has its own DPA for call audio/transcripts.
- **Quality / bias:** Ensure scripts and scenarios cover real cases (emergencies, accents, noise). Plan a sample of calls for training/configuration and testing.
- **Retention:** Retention period for recordings and transcriptions to be defined (GDPR and internal compliance). With our stack, we decide retention for our data; the voice provider’s policy applies to their data.

### 4.2 Skills and Resources

- **Internal:** One business referent (operations / reception) to define scenarios, transfer rules and validate reports; one IT referent for calendar integration and any APIs.
- **External:** Limova (configuration, training, support); possibly project support (AMOA) if needed.
- **Costs to quantify:** Limova subscription (per number / per site), implementation cost (configuration, integration), training.

### 4.3 Risks and Mitigation (Standard AI format)

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| User (team) rejection | Adoption failure, rollback | Medium | Involve teams from PoC; training; pilot period with gradual switchover |
| Poor call qualification (wrong transfers) | Caller frustration, wasted time | Medium | Refine scripts and rules with operations; regular review of reports and transfers |
| Calendar integration issues (availability, duplicates) | Appointments not created or conflicts | Low to medium | Dedicated PoC on test calendar; clear rules for slots and sync |
| GDPR / confidentiality non-compliance | Sanctions, reputation | Low if managed | DPA with vendor (Limova or voice provider); inform callers (“this call may be recorded and processed by AI”); defined retention; with our stack we control our data and logic |
| Higher cost than expected | Budget overrun | Medium | Set a cap for PoC/Pilot; compare offers (Limova, Vapi, Bland AI, Retell, etc.) in feasibility phase |

### 4.4 Compliance (GDPR / AI)

- **GDPR:** Purpose, data minimisation, access/rectification/erasure rights, legal basis (legitimate interest or consent as applicable). Document in a processing record “inbound call handling – AI agent”.
- **EU AI Regulation:** Classify the system (likely “limited risk”) and ensure transparency towards individuals (information that they are speaking to an AI agent).
- **Sector-specific:** Check that no sector norms (private security) impose specific constraints on recording or processing of calls.

---

## 5. Summary and Next Steps

### 5.1 Feasibility

- **Technical:** Feasible with a solution such as Limova Tom for reception, qualification, appointment booking, transfer and summary; scheduling and email are phase 2. An in-house build (Section 2.4) is also feasible and delivers transparency (no black box) and all features in one stack, including planning and email.
- **Organisational:** Feasible provided a dedicated business referent and IT referent for PoC/Pilot.
- **Economic:** To be validated with a Limova quote and internal estimate (configuration time, integration, training); an own stack avoids ongoing vendor lock-in and aligns cost with our control over logic and data.

### 5.2 Recommended MVP (recap)

- **Scope:** One pilot line / one site.
- **Functions (P0):** 24/7 reception, qualification, appointment booking (calendar), intelligent transfer, summary for callback.
- **Phase 2 (or included from day one with our stack):** Send/publish scheduling; automatic email replies.

### 5.3 Proposed Next Steps

1. **Validate** this study internally (management, operations, IT) and decide whether to launch the PoC—and whether to use **Limova** or **our own stack** (Section 2.4).
2. **If Limova:** contact Limova (Tom demo, quote, data hosting terms and DPA). **If our stack:** deploy our API, configure a voice provider (e.g. Vapi) with our webhook, and fill routing numbers in config.
3. **Define the pilot site/line** and the business + IT referents.
4. **Draft the PoC specification** (detailed scenarios, transfer rules, success KPIs).
5. **Launch the PoC** per the preliminary schedule (4–6 weeks), then run the Pilot (6–8 weeks) and the rollout decision.


