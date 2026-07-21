"""SQLite connection and initialization helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
from fastapi import Request

from app.core.config import settings
from app.db.seed import seed_data
from app.db.tables import TABLES


def database_path() -> Path:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// database URLs are supported in the MVP.")
    raw_path = url.removeprefix("sqlite:///")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


async def connect() -> aiosqlite.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def initialize_database() -> None:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        for statement in TABLES:
            await db.execute(statement)
        await seed_data(db)


async def get_db(request: Request) -> AsyncIterator[aiosqlite.Connection]:
    db = request.app.state.db
    yield db


@asynccontextmanager
async def lifespan(app):
    await initialize_database()
    app.state.db = await connect()
    try:
        yield
    finally:
        await app.state.db.close()
