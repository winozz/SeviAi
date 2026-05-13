"""One-time (idempotent) seed script for SeviAi SQLite database.

Run from the project root:
    python scripts/seed_db.py

Seeds the following tables in data/cavsu_intents.db:
    campus_places        -- from api/campus_places._PLACE_METADATA
    map_waypoints        -- from data/waypoints_override.json
    map_coords_overrides -- from data/coords_override.json
    map_custom_markers   -- from data/custom_markers.json
    seasons              -- hardcoded academic-calendar seasons

Uses INSERT OR REPLACE so re-running is safe.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow imports from the project root and api/ package
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from api.db import ensure_schema, get_conn
from api.campus_places import _PLACE_METADATA  # noqa: PLC0415

# ---------------------------------------------------------------------------
# Seasons data (inline — mirrors api/topic_recommender.SEASONS exactly)
# ---------------------------------------------------------------------------

_SEASONS_DATA = [
    {
        "key": "enrollment_first_sem",
        "label": "1st-semester enrollment is open",
        "reason": "Registration for the 1st semester runs until June 30.",
        "months": [5, 6],
        "tags": [
            "enrollment_procedure",
            "enrollment_schedule",
            "tuition_fees",
            "admissions_requirements",
            "scholarship",
            "registrar",
        ],
        "sort_order": 0,
    },
    {
        "key": "first_sem_start",
        "label": "First semester has started",
        "reason": "Classes began July 1 — orientation and schedule questions are common.",
        "months": [7, 8],
        "tags": [
            "academic_calendar",
            "courses_offered",
            "campus_facilities",
            "campus_location",
            "registrar",
            "scholarship",
        ],
        "sort_order": 1,
    },
    {
        "key": "first_sem_midterms",
        "label": "First semester — midterm period",
        "reason": "Midterms are underway — academic policy questions peak now.",
        "months": [9, 10],
        "tags": [
            "academic_policies",
            "academic_calendar",
            "registrar",
            "campus_facilities",
            "scholarship",
        ],
        "sort_order": 2,
    },
    {
        "key": "enrollment_second_sem",
        "label": "2nd-semester enrollment is open",
        "reason": "Registration for the 2nd semester runs November 15 – December 31.",
        "months": [11, 12],
        "tags": [
            "enrollment_procedure",
            "enrollment_schedule",
            "tuition_fees",
            "registrar",
            "academic_calendar",
            "scholarship",
        ],
        "sort_order": 3,
    },
    {
        "key": "second_sem_ongoing",
        "label": "Second semester is ongoing",
        "reason": "2nd semester is in session — common questions about courses and schedules.",
        "months": [1, 2, 3, 4],
        "tags": [
            "academic_calendar",
            "courses_offered",
            "academic_policies",
            "registrar",
            "campus_facilities",
            "scholarship",
        ],
        "sort_order": 4,
    },
]


def seed_campus_places(conn) -> int:
    cur = conn.cursor()
    count = 0
    for place_id, meta in _PLACE_METADATA.items():
        label = meta.get("full") or meta.get("short") or place_id
        cur.execute(
            """
            INSERT OR REPLACE INTO campus_places
                (place_id, label, num, short, full, walk_minutes, direction, x, y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                place_id,
                label,
                meta.get("num"),
                meta.get("short"),
                meta.get("full"),
                meta.get("walk_minutes_from_gate"),
                meta.get("direction_from_gate"),
                meta.get("x"),
                meta.get("y"),
            ),
        )
        count += 1
    conn.commit()
    return count


def seed_map_waypoints(conn) -> int:
    waypoints_path = _ROOT / "data" / "waypoints_override.json"
    if not waypoints_path.exists():
        print("  [SKIP] data/waypoints_override.json not found")
        return 0
    data: dict = json.loads(waypoints_path.read_text(encoding="utf-8")) or {}
    cur = conn.cursor()
    count = 0
    for wid, entry in data.items():
        if not isinstance(entry, dict):
            continue
        if "x" not in entry or "y" not in entry:
            continue
        neighbors = entry.get("neighbors", [])
        if not isinstance(neighbors, list):
            neighbors = []
        cur.execute(
            """
            INSERT OR REPLACE INTO map_waypoints (waypoint_id, x, y, neighbors)
            VALUES (?, ?, ?, ?)
            """,
            (wid, float(entry["x"]), float(entry["y"]), json.dumps(neighbors)),
        )
        count += 1
    conn.commit()
    return count


def seed_coords_overrides(conn) -> int:
    coords_path = _ROOT / "data" / "coords_override.json"
    if not coords_path.exists():
        return 0
    data: dict = json.loads(coords_path.read_text(encoding="utf-8")) or {}
    if not data:
        return 0
    cur = conn.cursor()
    count = 0
    for place_id, coords in data.items():
        if not isinstance(coords, dict):
            continue
        if "x" not in coords or "y" not in coords:
            continue
        cur.execute(
            "INSERT OR REPLACE INTO map_coords_overrides (place_id, x, y) VALUES (?, ?, ?)",
            (place_id, float(coords["x"]), float(coords["y"])),
        )
        count += 1
    conn.commit()
    return count


def seed_custom_markers(conn) -> int:
    markers_path = _ROOT / "data" / "custom_markers.json"
    if not markers_path.exists():
        return 0
    data: dict = json.loads(markers_path.read_text(encoding="utf-8")) or {}
    if not data:
        return 0
    cur = conn.cursor()
    count = 0
    for mid, marker in data.items():
        if not isinstance(marker, dict):
            continue
        cur.execute(
            """
            INSERT OR REPLACE INTO map_custom_markers (id, name, abbr, x, y, num)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(marker.get("id", mid)),
                str(marker.get("name", "")),
                str(marker.get("abbr", marker.get("name", ""))),
                float(marker.get("x", 0)),
                float(marker.get("y", 0)),
                marker.get("num"),
            ),
        )
        count += 1
    conn.commit()
    return count


def seed_seasons(conn) -> int:
    cur = conn.cursor()
    count = 0
    for s in _SEASONS_DATA:
        cur.execute(
            """
            INSERT OR REPLACE INTO seasons
                (key, label, reason, months, tags, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                s["key"],
                s["label"],
                s["reason"],
                json.dumps(s["months"]),
                json.dumps(s["tags"]),
                s["sort_order"],
            ),
        )
        count += 1
    conn.commit()
    return count


def main() -> None:
    print("=" * 60)
    print("  SeviAi DB Seed Script")
    print("=" * 60)

    print("\n[1/2] Ensuring schema...")
    ensure_schema()
    print("      Schema OK.")

    print("\n[2/2] Seeding tables...")
    with get_conn() as conn:
        n = seed_campus_places(conn)
        print(f"      campus_places        : {n} rows")

        n = seed_map_waypoints(conn)
        print(f"      map_waypoints        : {n} rows")

        n = seed_coords_overrides(conn)
        print(f"      map_coords_overrides : {n} rows")

        n = seed_custom_markers(conn)
        print(f"      map_custom_markers   : {n} rows")

        n = seed_seasons(conn)
        print(f"      seasons              : {n} rows")

    print("\nDone. DB is ready at data/cavsu_intents.db")


if __name__ == "__main__":
    main()
