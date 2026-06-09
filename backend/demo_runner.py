"""
Vita Roots — Demo Runner
========================
Runs a full end-to-end pipeline sequence against the four seeded demo families,
generating Phoenix Arize traces and triggering real Resend approval emails.

Usage:
  python demo_runner.py

Prerequisites:
  - Backend running on localhost:8000
  - MCP server running on localhost:8001
  - Supabase seeded with seed_demo_data_fixed.sql
  - .env contains PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_API_KEY,
    RESEND_API_KEY, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY

What this script does:
  1. Verifies all four demo families exist in Supabase
  2. Generates a meal plan for Rivera and Johnson-Williams families
  3. Triggers plan approval requests → fires Resend approval emails
  4. Runs a live PubMed research signal through the full MCP pipeline
     (fetch → match → score) against Rivera and Johnson-Williams
  5. Creates a support ticket for each family (one per category)
  6. Prints a summary of all Phoenix trace-generating events
"""

import asyncio
import json
import os
import sys
import time
from datetime import date, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()

API       = "http://localhost:8000"
MCP       = "http://localhost:8001"
TIMEOUT   =  120.0

# Demo family IDs (must match seed_demo_data_fixed.sql)
FAMILIES = {
    "rivera":   "a1000000-0000-0000-0000-000000000001",
    "johnson":  "a1000000-0000-0000-0000-000000000002",
    "chen":     "a1000000-0000-0000-0000-000000000003",
    "okafor":   "a1000000-0000-0000-0000-000000000004",
}

WEEK_START = (date.today() + timedelta(days=7 - date.today().weekday())).isoformat()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def ok(msg: str):
    print(f"  ✓  {msg}")

def warn(msg: str):
    print(f"  ⚠  {msg}")

def fail(msg: str):
    print(f"  ✗  {msg}")
    sys.exit(1)

async def get(client: httpx.AsyncClient, path: str) -> dict:
    r = await client.get(f"{API}{path}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

async def post(client: httpx.AsyncClient, path: str, body: dict, base: str = API) -> dict:
    r = await client.post(f"{base}{path}", json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

# ---------------------------------------------------------------------------
# Step 1 — Verify families exist
# ---------------------------------------------------------------------------

async def verify_families(client: httpx.AsyncClient):
    section("Step 1 — Verifying demo families in Supabase")
    for name, fid in FAMILIES.items():
        try:
            data = await get(client, f"/api/families/{fid}")
            family = data["data"]
            members_data = await get(client, f"/api/families/{fid}/members")
            members = members_data.get("data", [])
            ok(f"{family['name']} ({family['client_number']}) · {len(members)} member(s)")
        except Exception as e:
            fail(f"Family '{name}' not found — run seed_demo_data_fixed.sql first. Error: {e}")
# ---------------------------------------------------------------------------
# Step 2 — Generate meal plans (Rivera + Johnson-Williams)
# ---------------------------------------------------------------------------

async def generate_meal_plans(client: httpx.AsyncClient) -> dict:
    section("Step 2 — Generating meal plans (Rivera + Johnson-Williams)")
    plan_ids = {}

    for name in ("rivera", "johnson"):
        fid = FAMILIES[name]
        try:
            resp = await post(client, "/api/meal-plans/generate", {
                "family_id": fid,
                "week_start": WEEK_START,
            })
            plan_id = resp["data"]["id"]
            plan_ids[name] = plan_id
            ok(f"{name.capitalize()} meal plan generated — id: {plan_id[:8]}…")
        except Exception as e:
            warn(f"Could not generate meal plan for {name}: {e}")

    return plan_ids

# ---------------------------------------------------------------------------
# Step 3 — Trigger approval emails
# ---------------------------------------------------------------------------

async def trigger_approvals(client: httpx.AsyncClient, plan_ids: dict):
    section("Step 3 — Triggering plan approval gates + Resend emails")

    for name, plan_id in plan_ids.items():
        fid = FAMILIES[name]
        try:
            resp = await post(client, "/api/approvals/plan", {
                "family_id": fid,
                "meal_plan_id": plan_id,
            })
            data = resp["data"]
            email_sent = data.get("email_sent", False)
            token = data.get("token", "")[:8]

            if email_sent:
                ok(f"{name.capitalize()} — approval email sent · token: {token}…")
            else:
                warn(f"{name.capitalize()} — approval record created but email not sent "
                     f"(check RESEND_API_KEY and family email in Supabase)")
        except Exception as e:
            warn(f"Approval request failed for {name}: {e}")

    # Also trigger a grocery approval for Chen (to demo the market signal path)
    section("Step 3b — Grocery approval for Chen family (market signal path)")
    try:
        # Generate grocery list first — requires an existing meal plan
        meal_resp = await post(client, "/api/meal-plans/generate", {
            "family_id": FAMILIES["chen"],
            "week_start": WEEK_START,
        })
        chen_plan_id = meal_resp["data"]["id"]

        grocery_resp = await post(client, "/api/grocery-lists/generate", {
           "family_id": FAMILIES["chen"],
           "meal_plan_id": chen_plan_id,
           "budget": 220.0,
        })
        grocery_id = grocery_resp["data"]["id"]

        approval_resp = await post(client, "/api/approvals/grocery", {
            "family_id": FAMILIES["chen"],
            "grocery_list_id": grocery_id,
        })
        data = approval_resp["data"]
        email_sent = data.get("email_sent", False)
        if email_sent:
            ok(f"Chen — grocery approval email sent · {data.get('item_count', '?')} items · "
               f"${data.get('total_cost', 0):.2f}")
        else:
            warn("Chen — grocery approval record created but email not sent")
    except Exception as e:
        warn(f"Chen grocery approval skipped: {e}")

# ---------------------------------------------------------------------------
# Step 4 — Run research signal through MCP pipeline
# ---------------------------------------------------------------------------

async def run_research_signal(client: httpx.AsyncClient):
    section("Step 4 — Research signal pipeline (Phoenix traces)")

    # 4a: Fetch from PubMed
    print("\n  [4a] fetch_pubmed_research — omega-3 inflammation pregnancy")
    try:
        pubmed_resp = await post(client, "/tools/fetch_pubmed_research", {
            "keywords": ["omega-3", "inflammation", "pregnancy"],
            "max_results": 3,
            "days_back": 90,
        }, base=MCP)

        articles = pubmed_resp.get("articles", [])
        if not articles:
            warn("No PubMed articles returned — signal demo will use synthetic data")
            signal_title   = "Omega-3 supplementation reduces inflammatory markers in pregnant women"
            signal_summary = ("A randomized controlled trial found that omega-3 supplementation "
                              "significantly reduced inflammatory markers in pregnant women with "
                              "gestational diabetes. Sample size: 180 participants.")
            is_peer_reviewed = True
        else:
            article = articles[0]
            signal_title   = article["title"]
            signal_summary = (f"Published in {article['journal']} on {article['pub_date']}. "
                              f"Authors: {', '.join(article['authors'][:3])}.")
            is_peer_reviewed = article.get("is_peer_reviewed", True)
            ok(f"Article: {signal_title[:70]}…")
            ok(f"Journal: {article['journal']} · peer-reviewed: {is_peer_reviewed}")
    except Exception as e:
        warn(f"PubMed fetch failed: {e} — using synthetic signal")
        signal_title   = "Omega-3 supplementation reduces inflammatory markers in pregnant women"
        signal_summary = ("A randomized controlled trial found that omega-3 supplementation "
                          "significantly reduced inflammatory markers in pregnant women with "
                          "gestational diabetes. Sample size: 180 participants.")
        is_peer_reviewed = True

    # 4b: Match against Rivera family
    print(f"\n  [4b] match_family_profiles — Rivera family")
    try:
        match_resp = await post(client, "/tools/match_family_profiles", {
            "family_id": FAMILIES["rivera"],
            "signal_title": signal_title,
            "signal_summary": signal_summary,
            "signal_type": "research",
        }, base=MCP)
        rivera_matches = match_resp.get("match_count", 0)
        matched = match_resp.get("matched_members", [])
        ok(f"Rivera — {rivera_matches} member(s) matched")
        for m in matched:
            ok(f"  → {m['name']} ({m['member_number']}) · {m['match_count']} reasons: "
               f"{', '.join(m['match_reasons'][:2])}…")
    except Exception as e:
        warn(f"Profile match failed for Rivera: {e}")
        rivera_matches = 0

    # 4c: Match against Johnson-Williams family
    print(f"\n  [4c] match_family_profiles — Johnson-Williams family")
    try:
        match_resp = await post(client, "/tools/match_family_profiles", {
            "family_id": FAMILIES["johnson"],
            "signal_title": signal_title,
            "signal_summary": signal_summary,
            "signal_type": "research",
        }, base=MCP)
        johnson_matches = match_resp.get("match_count", 0)
        matched = match_resp.get("matched_members", [])
        ok(f"Johnson-Williams — {johnson_matches} member(s) matched")
        for m in matched:
            ok(f"  → {m['name']} ({m['member_number']}) · {m['match_count']} reasons: "
               f"{', '.join(m['match_reasons'][:2])}…")
    except Exception as e:
        warn(f"Profile match failed for Johnson-Williams: {e}")
        johnson_matches = 0

    total_matches = rivera_matches + johnson_matches

    # 4d: Score the signal
    print(f"\n  [4d] score_signal")
    try:
        score_resp = await post(client, "/tools/score_signal", {
            "signal_type": "research",
            "title": signal_title,
            "summary": signal_summary,
            "source_name": "PubMed",
            "matched_member_count": total_matches,
            "metadata": {
                "is_peer_reviewed": is_peer_reviewed,
                "sample_size": 180,
            },
        }, base=MCP)

        score        = score_resp.get("score", 0)
        recommendation = score_resp.get("recommendation", "unknown")
        breakdown    = score_resp.get("breakdown", [])

        ok(f"Score: {score} · Recommendation: {recommendation.upper()}")
        for line in breakdown:
            ok(f"  {line}")

        if recommendation == "fire":
            ok(f"Signal qualifies for alert — {total_matches} family member(s) affected across 2 families")
        else:
            warn(f"Signal suppressed (score {score} < threshold 5)")

    except Exception as e:
        warn(f"Signal scoring failed: {e}")

# ---------------------------------------------------------------------------
# Step 5 — Run market signal pipeline (Okafor family)
# ---------------------------------------------------------------------------

async def run_market_signal(client: httpx.AsyncClient):
    section("Step 5 — Market signal pipeline (Okafor family · budget-sensitive)")

    # 5a: Fetch market prices for Okafor staples
    print("\n  [5a] fetch_market_prices — Okafor family staples")
    try:
        price_resp = await post(client, "/tools/fetch_market_prices", {
            "items": ["chicken thighs", "plantains", "rice", "black-eyed peas", "vitamin D supplement"],
        }, base=MCP)
        signals = price_resp.get("price_signals", [])
        ok(f"Price data returned for {len(signals)} item(s)")
        for s in signals:
            ok(f"  → {s['item']} · monitoring flagged: {s.get('price_monitoring_needed', False)}")
    except Exception as e:
        warn(f"Market price fetch failed: {e}")

    # 5b: Score a synthetic market signal (price increase scenario)
    print("\n  [5b] score_signal — synthetic 18% chicken price increase")
    try:
        score_resp = await post(client, "/tools/score_signal", {
            "signal_type": "market",
            "title": "Chicken thigh prices projected to increase 18% over next 30 days",
            "summary": "Supply chain disruption due to avian influenza outbreak affecting Southeast US poultry suppliers.",
            "source_name": "USDA Agricultural Marketing Service",
            "matched_member_count": 4,
            "metadata": {
                "projected_increase_pct": 18,
                "supply_disruption_flag": True,
            },
        }, base=MCP)

        score          = score_resp.get("score", 0)
        recommendation = score_resp.get("recommendation", "unknown")
        breakdown      = score_resp.get("breakdown", [])

        ok(f"Score: {score} · Recommendation: {recommendation.upper()}")
        for line in breakdown:
            ok(f"  {line}")
    except Exception as e:
        warn(f"Market signal scoring failed: {e}")

# ---------------------------------------------------------------------------
# Step 6 — Create support tickets (one per category)
# ---------------------------------------------------------------------------

async def create_support_tickets(client: httpx.AsyncClient):
    section("Step 6 — Support agent tickets (Sage · Alex · Morgan)")

    tickets = [
        {
            "family_id": FAMILIES["okafor"],
            "subject": "Question about halal meal plan options",
            "initial_message": ("Hi, we follow a halal diet and I want to make sure all the "
                                "meal recommendations are appropriate for our family. "
                                "Can you explain how the system accounts for halal requirements?"),
            "category": "general",
            "label": "Okafor → Sage (general)",
        },
        {
            "family_id": FAMILIES["chen"],
            "subject": "Update Lin's supplement preferences",
            "initial_message": ("I need to update my wife Lin's supplement list. "
                                "She has started taking NAC in addition to her current supplements. "
                                "How do I add this to her profile? Our client number is VR-002003."),
            "category": "account",
            "label": "Chen → Alex (account)",
        },
        {
            "family_id": FAMILIES["rivera"],
            "subject": "Question about upgrading our plan",
            "initial_message": ("We are currently on the Family plan and I wanted to understand "
                                "what the Premium plan includes and whether it would be worth "
                                "upgrading for our family of three. Client number VR-002001."),
            "category": "billing",
            "label": "Rivera → Morgan (billing)",
        },
    ]

    for t in tickets:
        try:
            resp = await post(client, "/api/support/tickets", {
                "family_id":       t["family_id"],
                "subject":         t["subject"],
                "initial_message": t["initial_message"],
                "category":        t["category"],
            })
            data       = resp["data"]
            agent_name = data.get("agent_name", "?")
            ticket_id  = data.get("ticket_id", "?")[:8]
            response   = data.get("initial_response", "")[:80]
            ok(f"{t['label']} · ticket: {ticket_id}… · agent: {agent_name}")
            ok(f"  Response preview: {response}…")
        except Exception as e:
            warn(f"Ticket creation failed for {t['label']}: {e}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary():
    section("Demo Run Complete — Phoenix Trace Summary")
    print("""
  Every step above generated one or more Phoenix Arize trace spans.
  Open your Phoenix dashboard to view:

  app.phoenix.arize.com → capstone-demo project → Traces

  What to look for:
  ─────────────────────────────────────────────────────────
  ✓  Meal plan generation spans (WellnessAgent · claude-sonnet-4-6)
  ✓  Support agent spans (detect_category · generate_response)
     tagged with support.category and support.agent_name
  ✓  Signal scoring spans from MCP server tool calls
  ✓  family.id attributes on all family-specific spans

  Approval emails:
  ─────────────────────────────────────────────────────────
  ✓  Rivera family   → meal plan approval email
  ✓  Johnson-Williams → meal plan approval email
  ✓  Chen family     → grocery list approval email

  Check inboxes at the .demo addresses or your configured
  Resend account dashboard at resend.com/emails

  Demo family IDs for live API calls during presentation:
  ─────────────────────────────────────────────────────────
  Rivera          VR-002001   a1000000-…-000001
  Johnson-Williams VR-002002  a1000000-…-000002
  Chen            VR-002003   a1000000-…-000003
  Okafor          VR-002004   a1000000-…-000004
    """)

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

async def main():
    print("\n  Vita Roots — Demo Runner")
    print("  Checking backend availability…")

    async with httpx.AsyncClient() as client:
        try:
            health = await get(client, "/health")
            ok(f"Backend healthy · Phoenix: {health.get('phoenix_connected')} · "
               f"v{health.get('version')}")
        except Exception:
            fail("Backend not reachable at localhost:8000 — start uvicorn first.")

        try:
            mcp_health = await client.get(f"{MCP}/health", timeout=10)
            mcp_health.raise_for_status()
            ok("MCP server healthy at localhost:8001")
        except Exception:
            fail("MCP server not reachable at localhost:8001 — start mcp_server.py first.")

        await verify_families(client)
        plan_ids = await generate_meal_plans(client)

        if plan_ids:
            await trigger_approvals(client, plan_ids)
        else:
            warn("No meal plans generated — skipping approval emails")

        await run_research_signal(client)
        await run_market_signal(client)
        await create_support_tickets(client)

    print_summary()

if __name__ == "__main__":
    asyncio.run(main())
