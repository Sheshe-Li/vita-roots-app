"""
End-to-end pipeline test for Vita Roots Signal Harvester.
Tests all 5 MCP tools in sequence: fetch → match → score → compound_action.

Target family: Thompson (VR-002009) — CAD, statin CoQ10 depletion, perimenopause
Signal: CoQ10 depletion from statin use — matches perfectly.

Usage:
    python test_pipeline.py
"""

import asyncio
import json
import httpx

MCP_BASE = "http://localhost:8001"
FAMILY_ID = "a1000000-0000-0000-0000-000000000009"  # Thompson family


async def step(label: str, coro):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)
    result = await coro
    print(json.dumps(result, indent=2))
    return result


async def run():
    async with httpx.AsyncClient(timeout=60.0) as client:

        # ── Health check ────────────────────────────────────────────
        health = await client.get(f"{MCP_BASE}/health")
        health.raise_for_status()
        print("\n✅ MCP server is up:", health.json()["version"])

        # ── STEP 1: CATCH — fetch PubMed research ───────────────────
        pubmed_resp = await client.post(f"{MCP_BASE}/tools/fetch_pubmed_research", json={
            "keywords": ["CoQ10", "statin", "coenzyme Q10 depletion", "perimenopause"],
            "max_results": 5,
            "days_back": 90,
        })
        pubmed_resp.raise_for_status()
        pubmed = pubmed_resp.json()

        print(f"\n{'='*60}")
        print("  STEP 1: CATCH — fetch_pubmed_research")
        print('='*60)
        print(f"  Found {pubmed['count']} articles")
        for a in pubmed["articles"][:3]:
            print(f"  - [{a['pubmed_id']}] {a['title'][:80]}...")
            print(f"    Peer-reviewed: {a['is_peer_reviewed']}")

        # Use first article as our signal (or fallback to mock)
        if pubmed["articles"]:
            article = pubmed["articles"][0]
            signal_title = article["title"]
            signal_summary = (
                f"Research from {article['journal']} ({article['pub_date']}) on "
                f"CoQ10 depletion associated with statin use and implications for "
                f"cardiac and mitochondrial health."
            )
            is_peer_reviewed = article["is_peer_reviewed"]
        else:
            print("  ⚠️  No live PubMed results — using mock signal")
            signal_title = "Statin-induced CoQ10 depletion: implications for cardiac health and perimenopause"
            signal_summary = (
                "Meta-analysis of 12 RCTs (n=2,400) confirms statins reduce plasma CoQ10 by 40-50%. "
                "CoQ10 supplementation significantly reduces statin-related myopathy and fatigue. "
                "Perimenopausal women on statins show heightened depletion risk."
            )
            is_peer_reviewed = True

        # ── STEP 2: ENRICH — match family profiles ──────────────────
        match_resp = await client.post(f"{MCP_BASE}/tools/match_family_profiles", json={
            "family_id": FAMILY_ID,
            "signal_title": signal_title,
            "signal_summary": signal_summary,
            "signal_type": "research",
        })
        match_resp.raise_for_status()
        match = match_resp.json()

        print(f"\n{'='*60}")
        print("  STEP 2: ENRICH — match_family_profiles")
        print('='*60)
        print(f"  Matched {match['match_count']} members:")
        for m in match["matched_members"]:
            print(f"  - {m['name']} (age {m['age']}, {m['life_stage']})")
            for reason in m["match_reasons"]:
                print(f"    • {reason}")

        matched_members = match["matched_members"]
        matched_count = match["match_count"]

        # ── STEP 3: SEPARATE — score signal ─────────────────────────
        score_resp = await client.post(f"{MCP_BASE}/tools/score_signal", json={
            "signal_type": "research",
            "title": signal_title,
            "summary": signal_summary,
            "source_name": "PubMed",
            "matched_member_count": matched_count,
            "metadata": {
                "is_peer_reviewed": is_peer_reviewed,
                "sample_size": 2400,
            },
        })
        score_resp.raise_for_status()
        scored = score_resp.json()

        print(f"\n{'='*60}")
        print("  STEP 3: SEPARATE — score_signal")
        print('='*60)
        print(f"  Score: {scored['score']} / threshold {scored['threshold']}")
        print(f"  Recommendation: {scored['recommendation'].upper()}")
        for b in scored["breakdown"]:
            print(f"  {b}")

        if scored["recommendation"] != "fire":
            print("\n⛔ Signal suppressed — not crossing threshold. Pipeline stops here.")
            print("   (Try adjusting keywords or using the mock signal)")
            return

        print(f"\n🔥 Signal FIRED — score {scored['score']} >= {scored['threshold']}")

        # ── STEP 4: COMPOUND — orchestrate action ───────────────────
        print(f"\n{'='*60}")
        print("  STEP 4: COMPOUND — compound_action")
        print("  (This calls WellnessAgent → Supabase → signal_alert)")
        print("  ⏳ Generating meal plan via Claude... (may take 20-40s)")
        print('='*60)

        compound_resp = await client.post(
            f"{MCP_BASE}/tools/compound_action",
            json={
                "family_id": FAMILY_ID,
                "signal_title": signal_title,
                "signal_summary": signal_summary,
                "signal_type": "research",
                "score": scored["score"],
                "score_breakdown": scored["breakdown"],
                "matched_members": matched_members,
                "signal_metadata": {"is_peer_reviewed": is_peer_reviewed},
                "source_name": "PubMed",
            },
            timeout=120.0,
        )
        compound_resp.raise_for_status()
        compound = compound_resp.json()

        print(f"\n  Action taken: {compound['action_taken']}")
        print(f"  New meal plan ID: {compound['new_plan_id']}")
        print(f"  Signal alert ID: {compound['alert_id']}")
        print(f"  Phoenix trace ID: {compound['trace_id']}")
        print(f"  Completed at: {compound['completed_at']}")

        if compound.get("error"):
            print(f"\n  ⚠️  Error: {compound['error']}")
        else:
            print("\n✅ FULL PIPELINE COMPLETE")
            print("   → Check Phoenix at http://localhost:6006 for the trace")
            print(f"   → New meal plan {compound['new_plan_id']} pending HITL approval in Supabase")


if __name__ == "__main__":
    asyncio.run(run())
