"""PostgreSQL database connection with asyncpg."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

import asyncpg
from asyncpg import Pool

from api.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[Pool] = None


async def init_pool() -> Pool:
    """Initialize the database connection pool."""
    global _pool

    if _pool is None:
        logger.info("Creating database connection pool...")
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=5,
            max_size=settings.database_pool_size,
            max_inactive_connection_lifetime=300,
        )
        logger.info("Database pool created successfully")

    return _pool


async def close_pool():
    """Close the database connection pool."""
    global _pool

    if _pool:
        logger.info("Closing database connection pool...")
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def get_pool() -> Pool:
    """Get the database connection pool."""
    if _pool is None:
        await init_pool()
    return _pool


@asynccontextmanager
async def get_connection():
    """Get a database connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as connection:
        yield connection


async def execute(query: str, *args) -> str:
    """Execute a query and return status."""
    async with get_connection() as conn:
        return await conn.execute(query, *args)


async def fetch_one(query: str, *args) -> Optional[dict]:
    """Fetch a single row."""
    async with get_connection() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch_all(query: str, *args) -> list[dict]:
    """Fetch all rows."""
    async with get_connection() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def insert_one(table: str, data: dict[str, Any]) -> Any:
    """Insert a single row and return the ID."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(f"${i + 1}" for i in range(len(data)))
    values = list(data.values())

    query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        RETURNING id
    """

    async with get_connection() as conn:
        row = await conn.fetchrow(query, *values)
        return row["id"] if row else None
