"""
Vita Roots — MCP Signal Harvester Server
4 atomic tools for the signal harvesting pipeline:
  1. fetch_pubmed_research  — CATCH: research signals from PubMed
  2. fetch_market_prices    — CATCH: market price signals
  3. match_family_profiles  — ENRICH: cross-reference signal against family members
  4. score_signal           — SEPARATE: score signal against rubric, return fire/suppress

Each tool does ONE thing. No bundled judgment.
Run standalone: python mcp_server.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vita Roots MCP Signal Harvester",
    description="Atomic MCP tool endpoints for the signal harvesting pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "tasheena.aguilera@gmail.com")


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class PubMedRequest(BaseModel):
    keywords: list[str]
    max_results: int = 10
    days_back: int = 30


class MarketPriceRequest(BaseModel):
    items: list[str]


class MatchProfilesRequest(BaseModel):
    family_id: str
    signal_title: str
    signal_summary: str
    signal_type: str  # "research" | "market"


class ScoreSignalRequest(BaseModel):
    signal_type: str  # "research" | "market"
    title: str
    summary: str
    source_name: str
    matched_member_count: int
    metadata: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# TOOL 1: fetch_pubmed_research
# CATCH layer — research signal source
# One job: query PubMed, return raw articles. No scoring, no matching.
# ---------------------------------------------------------------------------

@app.post("/tools/fetch_pubmed_research")
async def fetch_pubmed_research(req: PubMedRequest) -> dict:
    """
    Fetch recent PubMed research publications by keyword.
    Returns raw article metadata — title, abstract, journal, pub date, authors.
    Does NOT score or match against family profiles.
    """
    query = " OR ".join(f'"{kw}"[All Fields]' for kw in req.keywords)
    min_date = datetime.now().strftime("%Y/%m/%d")

    logger.info(f"[fetch_pubmed_research] Querying PubMed: {query}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Search for article IDs
        search_resp = await client.get(
            f"{PUBMED_BASE}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": req.max_results,
                "retmode": "json",
                "sort": "pub_date",
                "email": PUBMED_EMAIL,
                "reldate": req.days_back,
                "datetype": "pdat",
            },
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()
        ids = search_data.get("esearchresult", {}).get("idlist", [])

        if not ids:
            logger.info("[fetch_pubmed_research] No articles found.")
            return {"articles": [], "query": query, "count": 0}

        # Step 2: Fetch article summaries
        summary_resp = await client.get(
            f"{PUBMED_BASE}/esummary.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "json",
                "email": PUBMED_EMAIL,
            },
        )
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()
        articles_raw = summary_data.get("result", {})

        articles = []
        for uid in ids:
            art = articles_raw.get(uid, {})
            if not art:
                continue
            articles.append({
                "pubmed_id": uid,
                "title": art.get("title", ""),
                "journal": art.get("fulljournalname", art.get("source", "")),
                "pub_date": art.get("pubdate", ""),
                "authors": [a.get("name", "") for a in art.get("authors", [])[:5]],
                "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                "source_name": "PubMed",
                "publication_types": art.get("pubtype", []),
                "is_peer_reviewed": any(
                    pt in ["Journal Article", "Clinical Trial", "Randomized Controlled Trial"]
                    for pt in art.get("pubtype", [])
                ),
                "sample_size_unknown": True,  # abstracts needed for sample size
            })

        logger.info(f"[fetch_pubmed_research] Returned {len(articles)} articles.")
        return {
            "articles": articles,
            "query": query,
            "count": len(articles),
            "fetched_at": datetime.utcnow().isoformat(),
        }


# ---------------------------------------------------------------------------
# TOOL 2: fetch_market_prices
# CATCH layer — market signal source
# One job: get current and projected prices for a list of items.
# Uses Open Food Facts for real data + heuristic projection.
# Does NOT match against family plans.
# ---------------------------------------------------------------------------

@app.post("/tools/fetch_market_prices")
async def fetch_market_prices(req: MarketPriceRequest) -> dict:
    """
    Fetch current price data and project trends for grocery/supplement items.
    Returns price signals per item. Does NOT filter against family plans.
    """
    logger.info(f"[fetch_market_prices] Checking prices for: {req.items}")

    results = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        for item in req.items:
            try:
                # Query Open Food Facts for product data
                resp = await client.get(
                    "https://world.openfoodfacts.org/cgi/search.pl",
                    params={
                        "search_terms": item,
                        "action": "process",
                        "json": 1,
                        "page_size": 3,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                products = data.get("products", [])

                # Build price signal from available data
                # Note: Open Food Facts doesn't have live pricing — we flag for monitoring
                results.append({
                    "item": item,
                    "products_found": len(products),
                    "sample_product": products[0].get("product_name", item) if products else item,
                    "categories": products[0].get("categories", "") if products else "",
                    "price_monitoring_needed": True,
                    "projected_increase_pct": None,  # Requires pricing API integration
                    "supply_disruption_flag": False,
                    "source": "Open Food Facts",
                    "note": "Live pricing requires commodity API (Alpha Vantage or similar). Flag for monitoring.",
                    "fetched_at": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.warning(f"[fetch_market_prices] Error fetching {item}: {e}")
                results.append({
                    "item": item,
                    "error": str(e),
                    "price_monitoring_needed": True,
                    "projected_increase_pct": None,
                    "supply_disruption_flag": False,
                })

    logger.info(f"[fetch_market_prices] Returned price data for {len(results)} items.")
    return {
        "price_signals": results,
        "count": len(results),
        "fetched_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# TOOL 3: match_family_profiles
# ENRICH layer — cross-reference signal against family member profiles
# One job: given a signal and a family_id, return which members are affected and why.
# Does NOT score. Does NOT decide whether to fire an alert.
# ---------------------------------------------------------------------------

@app.post("/tools/match_family_profiles")
async def match_family_profiles(req: MatchProfilesRequest) -> dict:
    """
    Cross-reference a signal against all family member profiles.
    Returns list of affected members with match reasons.
    Does NOT score the signal — that is score_signal's job.
    """
    logger.info(f"[match_family_profiles] Matching signal for family {req.family_id}")

    members = await database.get_family_members(req.family_id)
    if not members:
        return {
            "family_id": req.family_id,
            "matched_members": [],
            "match_count": 0,
            "signal_title": req.signal_title,
        }

    signal_text = f"{req.signal_title} {req.signal_summary}".lower()
    matched = []

    for member in members:
        match_reasons = []

        # Check health conditions
        for condition in (member.get("health_conditions") or []):
            if condition.lower() in signal_text:
                match_reasons.append(f"health condition: {condition}")

        # Check goals
        for goal in (member.get("goals") or []):
            if any(word in signal_text for word in goal.lower().split()):
                match_reasons.append(f"goal: {goal}")

        # Check current supplements (for research signals)
        if req.signal_type == "research":
            for supplement in (member.get("current_supplements") or []):
                if supplement.lower() in signal_text:
                    match_reasons.append(f"current supplement: {supplement}")

        # Check dietary style
        dietary_style = member.get("dietary_style", "")
        if dietary_style and dietary_style.lower() in signal_text:
            match_reasons.append(f"dietary style: {dietary_style}")

        # Check life stage (e.g. "pregnant", "elderly", "infant")
        life_stage = member.get("life_stage", "")
        if life_stage and life_stage.lower() in signal_text:
            match_reasons.append(f"life stage: {life_stage}")

        if match_reasons:
            matched.append({
                "member_id": str(member.get("id")),
                "member_number": member.get("member_number"),
                "name": member.get("name"),
                "age": member.get("age"),
                "life_stage": member.get("life_stage"),
                "match_reasons": match_reasons,
                "match_count": len(match_reasons),
            })

    logger.info(f"[match_family_profiles] {len(matched)} members matched.")
    return {
        "family_id": req.family_id,
        "signal_title": req.signal_title,
        "signal_type": req.signal_type,
        "matched_members": matched,
        "match_count": len(matched),
        "enriched_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# TOOL 4: score_signal
# SEPARATE layer — score signal against rubric, return fire or suppress
# One job: apply scoring criteria, return numeric score and recommendation.
# Does NOT create alerts. Does NOT modify any data.
# ---------------------------------------------------------------------------

@app.post("/tools/score_signal")
async def score_signal(req: ScoreSignalRequest) -> dict:
    """
    Score a signal against the Vita Roots rubric.
    Returns numeric score, breakdown, and fire/suppress recommendation.
    Does NOT create alerts or modify data — caller decides what to do with score.

    RESEARCH scoring rubric:
      +3  peer-reviewed journal article
      +2  sample size > 100 (if known)
      +3  directly matches >= 1 family member condition/goal/supplement
      +2  contradicts or modifies current plan
      -3  animal/in-vitro study only
      THRESHOLD: score >= 5 → fire alert

    MARKET scoring rubric:
      REQUIRED: item in active family plan
      +5  projected increase >= 15%
      +5  supply disruption flag
      THRESHOLD: score >= 5 → fire alert
    """
    logger.info(f"[score_signal] Scoring {req.signal_type} signal: {req.title[:60]}")

    score = 0
    breakdown = []
    signal_text = f"{req.title} {req.summary}".lower()

    if req.signal_type == "research":
        # +3 peer-reviewed
        source = req.source_name.lower()
        is_peer_reviewed = req.metadata.get("is_peer_reviewed", False)
        if is_peer_reviewed or any(s in source for s in ["pubmed", "journal", "lancet", "nejm", "jama", "bmj"]):
            score += 3
            breakdown.append("+3: peer-reviewed source")

        # +2 sample size > 100
        sample_size = req.metadata.get("sample_size")
        if sample_size and isinstance(sample_size, int) and sample_size > 100:
            score += 2
            breakdown.append(f"+2: sample size {sample_size} > 100")

        # +3 matches >= 1 family member
        if req.matched_member_count >= 1:
            score += 3
            breakdown.append(f"+3: matches {req.matched_member_count} family member(s)")

        # +2 contradicts or modifies current plan
        contradiction_keywords = ["contraindication", "avoid", "risk", "harmful", "linked to", "associated with", "warning", "caution", "reduces", "increases risk"]
        if any(kw in signal_text for kw in contradiction_keywords):
            score += 2
            breakdown.append("+2: may contradict or modify current plan")

        # -3 animal/in-vitro only
        noise_keywords = ["mouse", "mice", "rat", "rats", "in vitro", "cell culture", "animal model", "murine"]
        if any(kw in signal_text for kw in noise_keywords):
            score -= 3
            breakdown.append("-3: animal or in-vitro study")

        threshold = 5
        recommendation = "fire" if score >= threshold else "suppress"

    elif req.signal_type == "market":
        projected_increase = req.metadata.get("projected_increase_pct", 0) or 0
        supply_disruption = req.metadata.get("supply_disruption_flag", False)

        # Item must be in family plan (caller validates — matched_member_count > 0 means item is active)
        if req.matched_member_count == 0:
            return {
                "score": 0,
                "breakdown": ["item not in any active family plan"],
                "recommendation": "suppress",
                "threshold": 5,
                "signal_type": req.signal_type,
                "scored_at": datetime.utcnow().isoformat(),
            }

        if projected_increase >= 15:
            score += 5
            breakdown.append(f"+5: projected price increase {projected_increase}% >= 15%")

        if supply_disruption:
            score += 5
            breakdown.append("+5: supply disruption flag")

        threshold = 5
        recommendation = "fire" if score >= threshold else "suppress"

    else:
        raise HTTPException(status_code=400, detail=f"Unknown signal_type: {req.signal_type}")

    logger.info(f"[score_signal] Score: {score} → {recommendation}")
    return {
        "score": score,
        "breakdown": breakdown,
        "recommendation": recommendation,
        "threshold": threshold,
        "signal_type": req.signal_type,
        "title": req.title,
        "matched_member_count": req.matched_member_count,
        "scored_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "vita-roots-mcp-signal-harvester",
        "tools": [
            "fetch_pubmed_research",
            "fetch_market_prices",
            "match_family_profiles",
            "score_signal",
        ],
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8001, reload=True)
