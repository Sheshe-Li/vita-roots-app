# Vita Roots — Claude Code Project Context

> Upload this file to your Claude Code session in VS Code to give Claude full
> context on what has been built, what is in progress, and what remains.
> Last updated: June 2026 · Capstone Phase 2 in progress

---

## What This Project Is

**Vita Roots** is an AI-powered family wellness app and the capstone project for
the Intelligent Automation Immersive program (9BRAINS / Divergence Academy / Helm).

The core product: a **Signal Harvester** that monitors the world for changes in
medical research and market prices, matches those changes to real family wellness
profiles, and — when a signal crosses the fire threshold — automatically
regenerates the affected family's meal plan and queues it for human approval.

The rubric evaluates three pillars: Product Management, Systems Thinking, and
Compliance. Part 1 was demoed on May 14, 2026. Phase 2 build is now underway.

---

## Repository

- **GitHub:** `https://github.com/Sheshe-Li/vita-roots-app`
- **Local path:** `C:\Users\tashe\Vita-Roots-app`
- **WSL path:** `/mnt/c/Users/tashe/Vita-Roots-app`
- **Branch:** `master`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python · FastAPI · uvicorn |
| AI Agent | Anthropic `claude-sonnet-4-6` · tool use · prompt caching |
| MCP Server | FastAPI on port 8001 |
| Database | Supabase (PostgreSQL) via `supabase-py` 2.9.0 |
| Observability | Phoenix Arize · OpenTelemetry auto-instrumentation |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS |
| Email | Resend (transactional approval emails) |
| Containers | Docker Compose |
| Workflow | n8n (connected, needs Phase 2 fix) |
| Vector store | Pinecone (connected, Phase 2 enrichment) |

---

## File Structure (key files only)

```
Vita-Roots-app/
├── backend/
│   ├── main.py                  # FastAPI entrypoint, port 8000
│   ├── agent.py                 # WellnessAgent — meal plans, grocery, supplements, chat
│   ├── mcp_server.py            # MCP Signal Harvester, port 8001
│   ├── compound_agent.py        # NEW Phase 2 — compound action orchestrator
│   ├── database.py              # Supabase async helpers
│   ├── models.py                # Pydantic models + enums
│   ├── observability.py         # Phoenix Arize / OTEL setup
│   ├── routes/
│   │   ├── family.py            # Family + member CRUD
│   │   ├── meal_plans.py        # Meal plan generation + approval
│   │   ├── grocery.py           # Grocery list generation
│   │   ├── supplements.py       # Supplement guide generation
│   │   └── chat.py              # Streaming chat endpoint
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Landing page
│   │   ├── dashboard/page.tsx   # Family dashboard (port 3000)
│   │   ├── onboarding/page.tsx  # Family onboarding
│   │   └── support/page.tsx     # Support chat UI (port 3001)
│   └── package.json
├── product-brief.md             # Capstone deliverable
├── architecture.md              # Capstone deliverable
├── context.md                   # Capstone deliverable (< 60 lines)
├── signal-decision.md           # Capstone deliverable
├── compliance-note.md           # Capstone deliverable
├── DEMO_GUIDE.md                # Step-by-step demo instructions
├── docker-compose.yml
└── start.sh
```

---

## Supabase Schema (15 tables)

```
families                  client_number, budget_weekly, quality_preference, plan_frequency
family_members            life_stage, dietary_style, wellness_philosophy, dosha,
                          health_conditions[], goals[], current_supplements[]
meal_plans                week_start, days_json, approved, approved_at
grocery_lists             items_json, total_estimated_cost, budget_weekly, approved
supplement_guides         member_id, recommendations jsonb
plan_approvals            token, status (pending/approved/rejected/expired)
grocery_approvals         token, status
signals                   signal_type, title, summary, score, status, metadata
signal_alerts             family_id, signal_id, matched_members, new_plan_id, status
subscription_plans        name, price_monthly, features
family_subscriptions      family_id, plan_id, status
billing_history           family_id, amount, description
support_tickets           family_id, category, status (open/in_progress/resolved/closed)
support_messages          ticket_id, role (user/assistant/system), content
audit_log                 family_id, action, entity_type, entity_id, details jsonb
```

**Valid enum values (critical — Supabase rejects anything not in this list):**

```
quality_preference:    organic | conventional | local | whole_foods |
                       minimally_processed | budget_friendly
plan_frequency:        weekly | biweekly | monthly
life_stage:            infant | child | teen | adult | elderly | pregnant | postpartum
sex:                   male | female | other | prefer_not_to_say
activity_level:        sedentary | lightly_active | moderately_active |
                       very_active | extra_active
dietary_style:         omnivore | vegetarian | vegan | pescatarian | flexitarian |
                       keto | paleo | gluten_free | dairy_free | halal | kosher |
                       raw | whole_food_plant_based
wellness_philosophy:   ayurvedic | tcm | western_integrative | blend | no_preference
dosha_type:            vata | pitta | kapha | vata_pitta | pitta_kapha |
                       vata_kapha | tridoshic | unknown
signal_type:           research | market
signal_status:         pending | scored | alerted | dismissed | acted_on
alert_decision:        adopt | flag_revisit | stay_the_course | stock_up | substitute
ticket_category:       general | account | billing
ticket_status:         open | in_progress | resolved | closed
approval_status:       pending | approved | rejected | expired
```

---

## Test Families in Supabase (9 total)

| Client # | Family | Key conditions | Signal target |
|---|---|---|---|
| VR-002001 | The Rivera Family | Hashimoto's, leaky gut, chronic inflammation | Research: autoimmune |
| VR-002002 | The Johnson-Williams Family | Gestational diabetes, osteoporosis, ADHD | Research: prenatal |
| VR-002003 | The Chen Family | PCOS, exercise-induced asthma | Market: specialty supps |
| VR-002004 | The Okafor Family | Prediabetes, vitamin D deficiency, halal | Research: vitamin D |
| VR-002005 | The Washington Family | Type 2 diabetes, hypertension, high triglycerides | Research: T2D / omega-3 |
| VR-002006 | The Patel Family | PCOS, iron deficiency anemia, hypothyroidism | Research: PCOS / thyroid |
| VR-002007 | The Nguyen Family | Postpartum depression risk, gut dysbiosis, infant | Research: DHA / postpartum |
| VR-002008 | The Hernandez Family | ADHD, eczema, leaky gut (child), endometriosis | Research: ADHD / omega-3 |
| VR-002009 | The Thompson Family | CAD, statin CoQ10 depletion, perimenopause | Research: CoQ10 / statins |

**Demo family UUIDs:**
```
VR-002001  a1000000-0000-0000-0000-000000000001
VR-002002  a1000000-0000-0000-0000-000000000002
VR-002003  a1000000-0000-0000-0000-000000000003
VR-002004  a1000000-0000-0000-0000-000000000004
VR-002005  a1000000-0000-0000-0000-000000000005
VR-002006  a1000000-0000-0000-0000-000000000006
VR-002007  a1000000-0000-0000-0000-000000000007
VR-002008  a1000000-0000-0000-0000-000000000008
VR-002009  a1000000-0000-0000-0000-000000000009
```

---

## Signal Pipeline Architecture

```
CATCH           ENRICH              SEPARATE         COMPOUND
─────           ──────              ────────         ────────
fetch_pubmed    match_family        score_signal     compound_action
_research   →   _profiles       →   (rubric)     →   (NEW Phase 2)
                                    score ≥ 5
fetch_market                        → fire           → WellnessAgent
_prices     →   (same enricher)  →  score < 5        → new meal plan
                                    → suppress        → signal_alert
                                                      → audit_log
```

**Scoring rubric — research signals:**
- +3 peer-reviewed journal (PubMed / Journal Article / RCT)
- +2 sample size > 100 human subjects
- +3 direct match to ≥1 family member condition/goal/supplement
- +2 contradicts or modifies current plan
- -3 animal or in-vitro study only
- Threshold: score ≥ 5 → fire

**Scoring rubric — market signals:**
- Item must be in active family grocery list (required gate)
- +5 projected price increase ≥ 15%
- +5 supply disruption flag
- Threshold: score ≥ 5 → fire

---

## MCP Tools (port 8001)

| Endpoint | Layer | Job |
|---|---|---|
| `POST /tools/fetch_pubmed_research` | CATCH | Query PubMed by keyword, return article metadata |
| `POST /tools/fetch_market_prices` | CATCH | Check Open Food Facts, flag items for monitoring |
| `POST /tools/match_family_profiles` | ENRICH | Cross-reference signal text against member conditions/goals/supplements |
| `POST /tools/score_signal` | SEPARATE | Apply scoring rubric, return score + fire/suppress |
| `POST /tools/compound_action` | COMPOUND | Orchestrate full downstream action when signal fires **(NEW — Phase 2)** |

---

## WellnessAgent (agent.py)

Three structured output tools using Anthropic tool use:
- `create_meal_plan` — 7-day family plan as JSON
- `create_grocery_list` — categorized list from meal plan
- `create_supplement_guide` — personalized per member

Plus streaming chat via `agent.chat()`.

All calls use prompt caching on the system block (`cache_control: ephemeral`).
All calls are auto-traced by Phoenix Arize via OTEL.

---

## Support Agent System

Three specialist agents accessible via `POST /api/support/chat`:
- **Sage** — wellness & nutrition questions
- **Alex** — account & plan management
- **Morgan** — billing & subscription questions

Tickets persisted to `support_tickets` + `support_messages` tables.
Separate frontend at `localhost:3001/support`.

---

## HITL Approval Flow

1. Signal fires → `compound_action` creates `signal_alert` (status: pending)
2. Approval email sent via Resend with unique token link
3. In-app notification also created
4. Family clicks "Adopt" / "Flag & Revisit" / "Stay the Course"
5. Token resolves → `plan_approvals` updated → audit log written
6. If "Adopt" → new meal plan goes live

**Stakes × Reversibility:**
- Research signals → HIGH stakes / LOW reversibility → always require explicit approval
- Market signals → MEDIUM stakes / HIGH reversibility → 48hr auto-default to "stay the course"

---

## ✅ COMPLETED (Phase 1 — demoed May 14, 2026)

- [x] Supabase relational schema — 15 tables, all enums, audit log
- [x] 9 test families seeded with realistic health conditions
- [x] WellnessAgent — meal plan, grocery, supplement, streaming chat
- [x] 4 atomic MCP tools — fetch_pubmed_research, fetch_market_prices, match_family_profiles, score_signal
- [x] HITL approval flow — email (Resend) + in-app, token resolution
- [x] 3-agent customer support system (Sage / Alex / Morgan)
- [x] Support chat frontend (Next.js, port 3001)
- [x] Phoenix Arize observability — traces on all agent calls
- [x] Committed deliverable docs: product-brief.md, architecture.md, context.md, signal-decision.md, compliance-note.md
- [x] 10-slide capstone deck (VitaRoots_Capstone_Part1.pptx)
- [x] GitHub repo with daily commit cadence
- [x] Live demo — Johnson-Williams family (VR-002002), Destiny matched on gestational diabetes + inflammation, score 8, FIRE

---

## 🔄 IN PROGRESS (Phase 2 — current session)

- [x] Phase 2 seed data loaded — 5 new families (VR-002005 to VR-002009)
- [x] `compound_agent.py` written — wires score → WellnessAgent → Supabase persist → signal_alert
- [x] `POST /tools/compound_action` endpoint written for mcp_server.py
- [x] `create_signal`, `create_signal_alert`, `create_meal_plan` DB helpers written
- [ ] **NEXT:** Wire compound_agent.py into mcp_server.py and database.py (files delivered, not yet integrated)
- [ ] **NEXT:** Restart MCP server, test full pipeline end-to-end with a new family

---

## ❌ REMAINING (Phase 2 — not yet started)

### Block 2 — n8n + Pinecone enrichment
- [ ] Fix n8n workflow trigger (currently broken)
- [ ] Wire Pinecone semantic search into match_family_profiles for vector-based enrichment
- [ ] Replace keyword matching with embedding similarity in ENRICH layer

### Block 3 — Multi-agent handoff
- [ ] Signal Harvester → WellnessAgent context passing (partially done via compound_agent)
- [ ] WellnessAgent → Support Agent handoff (when a family asks about a fired signal)
- [ ] Shared context object passed between agents

### Block 4 — Observability hardening
- [ ] Phoenix trace coverage on compound_agent full chain (verify in UI)
- [ ] Confirm all 5 MCP tools show as child spans under one parent trace
- [ ] Update compliance-note.md to include compound_agent data flows

### Block 5 — Committed files
- [ ] `retrospective.md` — what shipped in Phase 2, what was cut, what's next
- [ ] Updated `architecture.md` — add compound layer to diagram
- [ ] Phase 2 demo deck (10 slides)

### Block 6 — Final demo
- [ ] End-to-end live demo: fetch_pubmed → match → score → compound_action → Phoenix trace
- [ ] Show all 3 agents in one demo flow
- [ ] Recorded backup video

---

## Local Dev Commands

```bash
# Start everything
cd /mnt/c/Users/tashe/Vita-Roots-app
./start.sh

# Or manually:
cd backend && source .venv/bin/activate

# Backend API (port 8000)
uvicorn main:app --reload --port 8000

# MCP server (port 8001)
python mcp_server.py

# Frontend (port 3000)
cd frontend && npm run dev

# Support frontend (port 3001 — if 3000 taken)
cd frontend && npm run dev -- --port 3001
```

---

## Environment Variables Required (.env in backend/)

```
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_ANON_KEY=
PHOENIX_API_KEY=
RESEND_API_KEY=
PUBMED_EMAIL=tasheena.aguilera@gmail.com
PINECONE_API_KEY=        # Phase 2 — needed for vector enrichment
```

---

## Key Decisions Made

1. **Vita Roots IS the capstone** — not a separate project
2. **Two signal types:** research (PubMed) and market (Open Food Facts proxy)
3. **Pinecone kept** for Phase 2 Enrich layer semantic search
4. **Langflow deprioritized** — not load-bearing for rubric
5. **HITL split by stakes:** research always requires approval, market has 48hr auto-default
6. **No Cubelet integration** — compliance training platform, wrong domain for wellness signal harvesting

---

## Rubric Scoring Reference (Phase 2 grading)

| Category | Points | Status |
|---|---|---|
| Signal Pipeline — compound action end-to-end | 25 | 🔄 in progress |
| Atomic Tools + Context Design | 15 | ✅ done |
| Signal vs Noise Logic | 15 | ✅ done |
| Product Management pillar | 10 | ✅ done |
| Systems Thinking pillar | 10 | 🔄 needs architecture.md update |
| Compliance pillar | 10 | 🔄 needs compliance-note.md update |
| Demo / Communication | 10 | ❌ not yet |
| Repo Quality | 5 | ✅ daily commits |
| **Total** | **100** | **Pass = 70** |
