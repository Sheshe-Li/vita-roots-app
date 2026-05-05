# Family Wellness App

An AI-powered family meal planning, grocery list, and supplement guidance application built with Anthropic Claude, FastAPI, Next.js, and Phoenix Arize observability.

---

## Project Overview

Family Wellness App helps families create personalized weekly meal plans, smart grocery lists, and holistic supplement guidance — all tailored to each family member's unique dietary style, wellness philosophy (Ayurvedic, TCM, Western integrative), health goals, and budget.

Every LLM call is automatically traced and observable via Phoenix Arize at `http://localhost:6006`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Network                              │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐    │
│  │  Next.js 14  │────▶│  FastAPI     │────▶│  Anthropic       │    │
│  │  Frontend    │     │  Backend     │     │  Claude API      │    │
│  │  :3000       │     │  :8000       │     │  (external)      │    │
│  └──────────────┘     └──────┬───────┘     └──────────────────┘    │
│                              │                                      │
│                              │ OTLP traces                         │
│                              ▼                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐    │
│  │  Langflow    │     │  Phoenix     │     │  Supabase        │    │
│  │  :7860       │     │  Arize :6006 │     │  PostgreSQL      │    │
│  └──────────────┘     └──────────────┘     └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- AI Agent: Anthropic Claude `claude-sonnet-4-6` (Python SDK) with prompt caching
- Backend: Python FastAPI + asyncpg
- Observability: Phoenix Arize + OpenInference Anthropic instrumentation
- Workflow Builder: Langflow (visual flow editor)
- Database: Supabase (PostgreSQL)
- Frontend: Next.js 14 + Tailwind CSS (TypeScript)
- Containers: Docker Compose

---

## Prerequisites

- **Docker** and **Docker Compose** (for the quick start)
- OR:
  - Python 3.11+
  - Node.js 18+
  - A Supabase project (free tier works)
- An **Anthropic API key** (`ANTHROPIC_API_KEY`)

---

## Quick Start with Docker

1. **Clone and configure:**

   ```bash
   cd Vita-Roots-app
   cp .env.example .env
   # Edit .env — add your ANTHROPIC_API_KEY and Supabase credentials
   ```

2. **Start all services:**

   ```bash
   docker-compose up --build
   ```

   This starts:
   - Phoenix Arize at http://localhost:6006
   - Langflow at http://localhost:7860
   - FastAPI backend at http://localhost:8000
   - Next.js frontend at http://localhost:3000

3. **Open the app:** http://localhost:3000

---

## Manual Setup (Backend)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys

# Run the API server
uvicorn main:app --reload --port 8000
```

The API docs are available at http://localhost:8000/docs

**Important:** `observability.init_observability()` is called at the very top of `main.py` before any other imports, ensuring the Anthropic SDK is instrumented before the first API call.

---

## Manual Setup (Frontend)

```bash
cd frontend

# Install dependencies
npm install

# Set environment variable
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Frontend available at http://localhost:3000

---

## Accessing Phoenix Arize

Phoenix provides full LLM observability — traces, spans, latency, token counts, and more.

- **URL:** http://localhost:6006
- **Project:** `Vita-Roots-app` (configurable via `PHOENIX_PROJECT_NAME`)

Every Anthropic API call made by the backend is automatically traced. You will see:
- Full request/response spans
- Token usage per call
- Latency breakdown
- Custom attributes: `family.id`, `family.member_id`, `wellness.request_type`, `llm.model`

No configuration required — the `AnthropicInstrumentor` wraps the SDK globally on startup.

---

## Accessing Langflow

Langflow provides a visual workflow builder for the meal planning agent flow.

- **URL:** http://localhost:7860
- **Default login:** `admin` / `wellness123` (change in docker-compose.yml for production)

**Importing the flow:**
1. Open Langflow at http://localhost:7860
2. Click "New Project" → "Import"
3. Select `langflow/wellness_agent_flow.json`
4. Set your `ANTHROPIC_API_KEY` in the Anthropic node
5. Click "Run" to test the flow

The flow visually represents: `Family Profile Input → Wellness System Prompt → Claude claude-sonnet-4-6 → [MealPlanGenerator | GroceryListGenerator | SupplementGuide] → Wellness Response`

---

## How QA / Observability Works

The Phoenix Arize integration uses OpenTelemetry + OpenInference:

1. On startup, `observability.init_observability()` registers a global `TracerProvider`
2. `AnthropicInstrumentor().instrument(tracer_provider=...)` patches the Anthropic SDK
3. Every `client.messages.create()` and `client.messages.stream()` call automatically creates a span
4. Custom wellness attributes are added to spans via `add_wellness_attributes()`
5. Spans are exported via OTLP HTTP to Phoenix at `http://phoenix:6006/v1/traces`
6. View all traces in the Phoenix UI → Projects → Vita-Roots-app

**Span attributes tracked:**
| Attribute | Values |
|-----------|--------|
| `family.id` | UUID of the family |
| `family.member_id` | UUID of the family member |
| `wellness.request_type` | `meal_plan` \| `grocery` \| `supplement` \| `chat` |
| `llm.model` | `claude-sonnet-4-6` |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes (for DB) |
| `SUPABASE_KEY` | Supabase anon key | Yes (for DB) |
| `SUPABASE_DB_PASSWORD` | Supabase DB password (for direct asyncpg) | Yes (for DB) |
| `PHOENIX_COLLECTOR_ENDPOINT` | OTLP endpoint for Phoenix | No (default: `http://phoenix:6006/v1/traces`) |
| `PHOENIX_PROJECT_NAME` | Phoenix project name | No (default: `Vita-Roots-app`) |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | No (default: `http://localhost:8000`) |

---

## API Reference

### Family
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/families` | Create family |
| GET | `/api/families/{id}` | Get family |
| PUT | `/api/families/{id}` | Update family |
| DELETE | `/api/families/{id}` | Delete family |
| POST | `/api/families/{id}/members` | Add member |
| GET | `/api/families/{id}/members` | List members |
| PUT | `/api/families/{id}/members/{mid}` | Update member |
| DELETE | `/api/families/{id}/members/{mid}` | Delete member |

### Meal Plans
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/meal-plans/generate` | Generate 7-day plan |
| GET | `/api/meal-plans/{id}` | Get saved plan |
| POST | `/api/meals/{id}/swap` | Swap a meal |

### Grocery
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/grocery-lists/generate` | Generate from meal plan |
| GET | `/api/grocery-lists/{plan_id}` | Get list |
| PATCH | `/api/grocery-items/{id}/check` | Toggle checked |

### Supplements
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/supplements/generate/{member_id}` | Generate guide |
| GET | `/api/supplements/{member_id}` | Get saved guide |

### Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Streaming SSE chat |

### System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check + Phoenix status |
| GET | `/docs` | Interactive API docs (Swagger) |

---

## Key Design Decisions

**Prompt caching:** The system prompt is sent with `cache_control: {"type": "ephemeral"}` on the system block. Claude caches the prompt after the first request, dramatically reducing latency and cost for subsequent calls within the cache window.

**Tool use for structured outputs:** Rather than prompting for JSON and parsing it, all structured endpoints (meal plans, grocery lists, supplements) use Anthropic tool use (`tool_choice: {"type": "any"}`), which guarantees schema-valid JSON output.

**Observability-first:** `init_observability()` is the very first call in `main.py` — before any other module imports — ensuring 100% of Anthropic SDK calls are instrumented.

**Graceful DB degradation:** If Supabase is unavailable, the app logs a warning and operates without persistent storage rather than crashing.

---

## Disclaimer

This application provides informational wellness guidance only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider before making dietary or supplement changes.
