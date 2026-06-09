"""
Quick connectivity test for all .env services.
Run: python test_env.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

results = []


def check(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    msg = f"{icon}  {name}"
    if detail:
        msg += f"  —  {detail}"
    print(msg)
    results.append(ok)


# ── 1. Anthropic ──────────────────────────────────────────────────────────────
def test_anthropic():
    try:
        import anthropic
        key = os.getenv("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=key)
        resp = client.models.list()
        models = [m.id for m in resp.data][:3]
        check("Anthropic API", True, f"models visible: {', '.join(models)}")
    except Exception as e:
        check("Anthropic API", False, str(e))


# ── 2. Supabase ───────────────────────────────────────────────────────────────
def test_supabase():
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", "")
        sb = create_client(url, key)
        resp = sb.table("families").select("client_number").limit(1).execute()
        row = resp.data[0]["client_number"] if resp.data else "(empty table)"
        check("Supabase DB", True, f"families table reachable, first row: {row}")
    except Exception as e:
        check("Supabase DB", False, str(e))


# ── 3. Phoenix / OTLP ─────────────────────────────────────────────────────────
def test_phoenix():
    try:
        import httpx
        endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "")
        api_key  = os.getenv("PHOENIX_API_KEY", "")
        project  = os.getenv("PHOENIX_PROJECT_NAME", "vita-roots-app")

        # Phoenix Cloud healthcheck lives at the root URL (strip /v1/traces)
        base = endpoint.replace("/v1/traces", "").rstrip("/")
        headers = {"api_key": api_key} if api_key else {}
        resp = httpx.get(f"{base}/healthz", headers=headers, timeout=10)
        ok = resp.status_code < 400
        check(
            "Phoenix Arize",
            ok,
            f"endpoint={endpoint}  project={project}  status={resp.status_code}",
        )
    except Exception as e:
        check("Phoenix Arize", False, str(e))


# ── 4. Resend ─────────────────────────────────────────────────────────────────
def test_resend():
    try:
        import httpx
        key = os.getenv("RESEND_API_KEY", "")
        resp = httpx.get(
            "https://api.resend.com/domains",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        ok = resp.status_code == 200
        data = resp.json()
        domains = [d.get("name") for d in data.get("data", [])]
        detail = f"domains={domains}" if domains else f"status={resp.status_code}"
        check("Resend Email", ok, detail)
    except Exception as e:
        check("Resend Email", False, str(e))


# ── run all ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Vita Roots — .env connectivity check ===\n")
    test_anthropic()
    test_supabase()
    test_phoenix()
    test_resend()

    passed = sum(results)
    total  = len(results)
    print(f"\n{passed}/{total} services connected")
    sys.exit(0 if passed == total else 1)
