"""
Database layer — Supabase (PostgreSQL via asyncpg).
Provides an async connection pool and helper functions for CRUD operations.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional
from uuid import UUID

import asyncpg
from asyncpg import Pool, Record

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None


async def get_pool() -> Pool:
    """Return (or create) the global asyncpg connection pool."""
    global _pool
    if _pool is None:
        _pool = await _create_pool()
    return _pool


async def _create_pool() -> Pool:
    """Create asyncpg pool from SUPABASE_URL env var."""
    supabase_url = os.getenv("SUPABASE_URL", "")
    # Supabase connection string format:
    # postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
    # Alternatively accept a raw DSN in DATABASE_URL
    dsn = os.getenv("DATABASE_URL") or _supabase_url_to_dsn(supabase_url)

    if not dsn:
        logger.warning(
            "No database DSN configured. Running without persistent storage."
        )
        return None  # type: ignore[return-value]

    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=2,
        max_size=10,
        command_timeout=60,
        init=_init_connection,
    )
    logger.info("asyncpg pool created successfully.")
    await _ensure_schema(pool)
    return pool


def _supabase_url_to_dsn(supabase_url: str) -> str:
    """
    Convert a Supabase project URL (https://xxx.supabase.co) to a PostgreSQL DSN.
    Requires SUPABASE_DB_PASSWORD env var to be set.
    """
    if not supabase_url:
        return ""
    # Extract project ref from URL
    try:
        ref = supabase_url.replace("https://", "").split(".")[0]
        password = os.getenv("SUPABASE_DB_PASSWORD", "")
        return f"postgresql://postgres:{password}@db.{ref}.supabase.co:5432/postgres"
    except Exception:
        return ""


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Configure each connection — enable JSON codec."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def _ensure_schema(pool: Pool) -> None:
    """Create tables if they don't exist (idempotent)."""
    ddl = """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS families (
        id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name        TEXT NOT NULL,
        data        JSONB NOT NULL DEFAULT '{}',
        created_at  TIMESTAMPTZ DEFAULT NOW(),
        updated_at  TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS family_members (
        id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        family_id   UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        name        TEXT NOT NULL,
        data        JSONB NOT NULL DEFAULT '{}',
        created_at  TIMESTAMPTZ DEFAULT NOW(),
        updated_at  TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS meal_plans (
        id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        family_id   UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        week_start  DATE NOT NULL,
        data        JSONB NOT NULL DEFAULT '{}',
        created_at  TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS grocery_lists (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        family_id       UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        meal_plan_id    UUID REFERENCES meal_plans(id) ON DELETE SET NULL,
        data            JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS supplement_guides (
        id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        family_id   UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        member_id   UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
        data        JSONB NOT NULL DEFAULT '{}',
        created_at  TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS chat_sessions (
        id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        family_id   UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        member_id   UUID REFERENCES family_members(id) ON DELETE SET NULL,
        messages    JSONB NOT NULL DEFAULT '[]',
        created_at  TIMESTAMPTZ DEFAULT NOW(),
        updated_at  TIMESTAMPTZ DEFAULT NOW()
    );
    """
    async with pool.acquire() as conn:
        await conn.execute(ddl)
    logger.info("Database schema verified.")


async def close_pool() -> None:
    """Close the connection pool on shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("asyncpg pool closed.")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


async def fetch_one(query: str, *args: Any) -> Optional[Record]:
    pool = await get_pool()
    if pool is None:
        return None
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetch_all(query: str, *args: Any) -> list[Record]:
    pool = await get_pool()
    if pool is None:
        return []
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute(query: str, *args: Any) -> str:
    pool = await get_pool()
    if pool is None:
        return "SKIP"
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def execute_returning(query: str, *args: Any) -> Optional[Record]:
    pool = await get_pool()
    if pool is None:
        return None
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


# ---------------------------------------------------------------------------
# Family-specific queries
# ---------------------------------------------------------------------------


async def create_family(data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        "INSERT INTO families (id, name, data) VALUES ($1, $2, $3) RETURNING *",
        str(data["id"]),
        data["name"],
        data,
    )


async def get_family(family_id: str) -> Optional[Record]:
    return await fetch_one(
        "SELECT * FROM families WHERE id = $1", family_id
    )


async def update_family(family_id: str, data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        """UPDATE families SET data = $1, name = $2, updated_at = NOW()
           WHERE id = $3 RETURNING *""",
        data,
        data.get("name", ""),
        family_id,
    )


async def delete_family(family_id: str) -> str:
    return await execute("DELETE FROM families WHERE id = $1", family_id)


async def list_families() -> list[Record]:
    return await fetch_all("SELECT * FROM families ORDER BY created_at DESC")


# ---------------------------------------------------------------------------
# Member-specific queries
# ---------------------------------------------------------------------------


async def create_member(family_id: str, data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        """INSERT INTO family_members (id, family_id, name, data)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        str(data["id"]),
        family_id,
        data["name"],
        data,
    )


async def get_member(member_id: str) -> Optional[Record]:
    return await fetch_one(
        "SELECT * FROM family_members WHERE id = $1", member_id
    )


async def get_family_members(family_id: str) -> list[Record]:
    return await fetch_all(
        "SELECT * FROM family_members WHERE family_id = $1 ORDER BY created_at",
        family_id,
    )


async def update_member(member_id: str, data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        """UPDATE family_members SET data = $1, name = $2, updated_at = NOW()
           WHERE id = $3 RETURNING *""",
        data,
        data.get("name", ""),
        member_id,
    )


async def delete_member(member_id: str) -> str:
    return await execute("DELETE FROM family_members WHERE id = $1", member_id)


# ---------------------------------------------------------------------------
# Meal plan queries
# ---------------------------------------------------------------------------


async def save_meal_plan(data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        """INSERT INTO meal_plans (id, family_id, week_start, data)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        str(data["id"]),
        str(data["family_id"]),
        data["week_start"],
        data,
    )


async def get_meal_plan(plan_id: str) -> Optional[Record]:
    return await fetch_one("SELECT * FROM meal_plans WHERE id = $1", plan_id)


async def get_family_meal_plans(family_id: str) -> list[Record]:
    return await fetch_all(
        "SELECT * FROM meal_plans WHERE family_id = $1 ORDER BY week_start DESC",
        family_id,
    )


# ---------------------------------------------------------------------------
# Grocery list queries
# ---------------------------------------------------------------------------


async def save_grocery_list(data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        """INSERT INTO grocery_lists (id, family_id, meal_plan_id, data)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        str(data["id"]),
        str(data["family_id"]),
        str(data["meal_plan_id"]),
        data,
    )


async def get_grocery_list(list_id: str) -> Optional[Record]:
    return await fetch_one("SELECT * FROM grocery_lists WHERE id = $1", list_id)


async def get_grocery_list_by_plan(plan_id: str) -> Optional[Record]:
    return await fetch_one(
        "SELECT * FROM grocery_lists WHERE meal_plan_id = $1 ORDER BY created_at DESC LIMIT 1",
        plan_id,
    )


async def update_grocery_list_data(list_id: str, data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        "UPDATE grocery_lists SET data = $1 WHERE id = $2 RETURNING *",
        data,
        list_id,
    )


# ---------------------------------------------------------------------------
# Supplement guide queries
# ---------------------------------------------------------------------------


async def save_supplement_guide(data: dict[str, Any]) -> Optional[Record]:
    return await execute_returning(
        """INSERT INTO supplement_guides (id, family_id, member_id, data)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        str(data["id"]),
        str(data["family_id"]),
        str(data["member_id"]),
        data,
    )


async def get_supplement_guide(member_id: str) -> Optional[Record]:
    return await fetch_one(
        "SELECT * FROM supplement_guides WHERE member_id = $1 ORDER BY created_at DESC LIMIT 1",
        member_id,
    )
