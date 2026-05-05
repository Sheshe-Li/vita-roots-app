# Architecture — Vita Roots Signal Harvester

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CATCH LAYER                                          │
│                                                                             │
│  ┌─────────────────────┐        ┌──────────────────────────┐               │
│  │  Research Catcher   │        │   Market Catcher         │               │
│  │  MCP Tool           │        │   MCP Tool               │               │
│  │                     │        │                          │               │
│  │  • PubMed API       │        │  • Commodity price APIs  │               │
│  │  • arXiv feed       │        │  • Supplement pricing    │               │
│  │  • RSS polling      │        │  • Trend forecasting     │               │
│  └──────────┬──────────┘        └─────────────┬────────────┘               │
│             │                                  │                            │
└─────────────┼──────────────────────────────────┼────────────────────────────┘
              │                                  │
              ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENRICH LAYER                                         │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Family Profile Matcher (MCP Tool)                                   │  │
│  │  • Cross-references signal against active family member profiles     │  │
│  │  • Identifies affected members by: health_conditions, goals,        │  │
│  │    dietary_style, wellness_philosophy, current_supplements,          │  │
│  │    active grocery items                                              │  │
│  │  • Attaches enriched context: member names, plan IDs, budget impact │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SEPARATE LAYER                                       │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Signal Scorer (MCP Tool)                                            │  │
│  │                                                                      │  │
│  │  RESEARCH scoring criteria:                                          │  │
│  │  • Peer-reviewed journal (not preprint): +3                         │  │
│  │  • Sample size > 100 human subjects: +2                             │  │
│  │  • Direct condition/goal match for ≥1 family member: +3            │  │
│  │  • Contradicts current plan: +2 (high urgency)                     │  │
│  │  • Animal/in-vitro study only: -3                                   │  │
│  │  • Threshold to fire alert: score ≥ 5                               │  │
│  │                                                                      │  │
│  │  MARKET scoring criteria:                                            │  │
│  │  • Item in active grocery or supplement list: required              │  │
│  │  • Projected price increase ≥ 15%: fire alert                      │  │
│  │  • Projected price increase < 15%: suppress (noise)                │  │
│  │  • Supply disruption flag: always fire                              │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     APPROVAL GATE (Human-in-the-Loop)                       │
│                                                                             │
│  Stakes × Reversibility Map:                                                │
│  • Research: HIGH stakes (health) × LOW reversibility → always require     │
│    explicit human approval before regenerating any plan                     │
│  • Market: MEDIUM stakes (cost) × HIGH reversibility → present options,    │
│    default to "stay the course" if no response within 48hrs                │
│                                                                             │
│  Approval actions:                                                          │
│  • "Adopt new direction" → triggers WellnessAgent plan regeneration        │
│  • "Flag and revisit" → stores signal, resurfaces in 30 days               │
│  • "Stay the course" → dismisses signal, logs decision                     │
│  • "Stock up" → updates grocery list quantity for affected items           │
│  • "Substitute" → triggers WellnessAgent grocery regeneration              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPOUND LAYER                                       │
│                                                                             │
│  ┌──────────────────────┐    ┌──────────────────────────────────────────┐  │
│  │  WellnessAgent       │    │  Notification / Alert Surface            │  │
│  │  (existing)          │    │  • Next.js frontend alert card           │  │
│  │                      │    │  • ChatAssistant SSE message             │  │
│  │  generate_meal_plan  │    │  • Decision buttons: Adopt / Flag /      │  │
│  │  generate_grocery    │◄───│    Stay the Course / Stock Up /          │  │
│  │  generate_supplement │    │    Substitute                            │  │
│  └──────────────────────┘    └──────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY (Phoenix Arize)                           │
│  Every signal event creates a span with:                                    │
│  • signal.type: research | market                                           │
│  • signal.score: numeric score from scorer                                  │
│  • family.id, family.member_id                                              │
│  • wellness.request_type, llm.model                                         │
│  • approval.decision: adopt | flag | stay | stock_up | substitute          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Failure Modes & Bottlenecks

| Failure Mode | Where It Breaks | Mitigation |
|---|---|---|
| PubMed API rate limit | Catch layer | Exponential backoff + cache last fetch timestamp |
| False positive research signal | Separate layer | Conservative threshold (≥5), LLM secondary review |
| Price API outage | Catch layer | Graceful degradation — skip market signals, log warning |
| Family has no active plan | Enrich layer | Check for active plan before enriching; skip if none |
| User ignores approval gate | Compound layer | 48hr timeout with logged default action |
| Supabase unavailable | All layers | In-memory mode (existing graceful degradation) |
| LLM context overflow | Enrich layer | Cap family context to 10 members max per request |
| Trace export failure | Observability | ConsoleSpanExporter fallback already implemented |

## Tech Stack
- **Signal Catchers:** Python MCP server endpoints (4+ atomic tools)
- **Backend:** FastAPI + WellnessAgent (existing)
- **Database:** Supabase PostgreSQL (existing)
- **Frontend:** Next.js 14 + Tailwind (existing)
- **Observability:** Phoenix Arize Cloud via OTLP HTTP
- **Model:** Anthropic claude-sonnet-4-6 with prompt caching
