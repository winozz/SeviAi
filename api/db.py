"""Central database module for SeviAi / CvSU chatbot.

Single source of truth for the SQLite connection and schema for all non-intent
tables. The intent tables (intents, patterns, responses) are managed by
intents_db.py at the project root; this module adds the five new tables.

DB path: data/cavsu_intents.db  (shared with intents_db.py)
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

# Resolve DB path relative to this file (api/ -> project root -> data/)
_DB_PATH: Path = Path(__file__).resolve().parent.parent / "data" / "cavsu_intents.db"

DB_PATH: str = str(_DB_PATH)


def get_conn() -> sqlite3.Connection:
    """Return a new SQLite connection to the shared chatbot DB."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS campus_places (
    place_id  TEXT PRIMARY KEY,
    label     TEXT NOT NULL,
    num       INTEGER,
    short     TEXT,
    full      TEXT,
    walk_minutes INTEGER,
    direction TEXT,
    x         INTEGER,
    y         INTEGER
);

CREATE TABLE IF NOT EXISTS map_waypoints (
    waypoint_id TEXT PRIMARY KEY,
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    neighbors   TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS map_coords_overrides (
    place_id TEXT PRIMARY KEY,
    x        REAL NOT NULL,
    y        REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS map_custom_markers (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    abbr TEXT NOT NULL,
    x    REAL NOT NULL,
    y    REAL NOT NULL,
    num  INTEGER
);

CREATE TABLE IF NOT EXISTS seasons (
    key        TEXT PRIMARY KEY,
    label      TEXT NOT NULL,
    reason     TEXT NOT NULL,
    months     TEXT NOT NULL,
    tags       TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);
"""


def ensure_schema() -> None:
    """Create all tables (if not already present) in the shared DB."""
    with get_conn() as conn:
        conn.executescript(_SCHEMA_SQL)
