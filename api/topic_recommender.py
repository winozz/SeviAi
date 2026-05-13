"""Date-aware topic recommendations for the DIWA homepage.

CvSU Academic Calendar:
  First Semester  : July – December
    Registration  : May 15 – June 30
    Classes start : July 1
    Commencement  : December 15-16

  Second Semester : January – June
    Registration  : November 15 – December 31
    Classes start : January 2
    Commencement  : May 25-26

We surface the topics most likely to be on the visitor's mind right now,
before they type. Falls back to a balanced default when nothing strongly
matches the current month.
"""

from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional


# ---------------------------------------------------------------------------
# Seasonal program — keep this in sync with the academic calendar intent and
# any official announcements. Each season carries:
#   - a human label for the UI heading
#   - a short reason string ("Enrollment is open this week")
#   - ranked tags (highest first)
# ---------------------------------------------------------------------------

class Season:
    __slots__ = ("key", "label", "reason", "tags")

    def __init__(self, key: str, label: str, reason: str, tags: List[str]):
        self.key = key
        self.label = label
        self.reason = reason
        self.tags = tags


SEASONS: List[Season] = [
    # May–June: 1st sem registration open (May 15 – June 30)
    Season(
        key="enrollment_first_sem",
        label="1st-semester enrollment is open",
        reason="Registration for the 1st semester runs until June 30.",
        tags=[
            "enrollment_procedure",
            "enrollment_schedule",
            "tuition_fees",
            "admissions_requirements",
            "scholarship",
            "registrar",
        ],
    ),
    # July–August: 1st sem just started (classes begin July 1)
    Season(
        key="first_sem_start",
        label="First semester has started",
        reason="Classes began July 1 — orientation and schedule questions are common.",
        tags=[
            "academic_calendar",
            "courses_offered",
            "campus_facilities",
            "campus_location",
            "registrar",
            "scholarship",
        ],
    ),
    # September–October: 1st sem midterms
    Season(
        key="first_sem_midterms",
        label="First semester — midterm period",
        reason="Midterms are underway — academic policy questions peak now.",
        tags=[
            "academic_policies",
            "academic_calendar",
            "registrar",
            "campus_facilities",
            "scholarship",
        ],
    ),
    # November–December: 1st sem ending + 2nd sem registration opens (Nov 15–Dec 31)
    # + 1st sem commencement (Dec 15-16)
    Season(
        key="enrollment_second_sem",
        label="2nd-semester enrollment is open",
        reason="Registration for the 2nd semester runs November 15 – December 31.",
        tags=[
            "enrollment_procedure",
            "enrollment_schedule",
            "tuition_fees",
            "registrar",
            "academic_calendar",
            "scholarship",
        ],
    ),
    # January–April: 2nd sem ongoing (classes start Jan 2, midterms ~Mar)
    Season(
        key="second_sem_ongoing",
        label="Second semester is ongoing",
        reason="2nd semester is in session — common questions about courses and schedules.",
        tags=[
            "academic_calendar",
            "courses_offered",
            "academic_policies",
            "registrar",
            "campus_facilities",
            "scholarship",
        ],
    ),
]


def load_seasons_from_db() -> List[Season]:
    """Load seasons from the DB `seasons` table.

    Returns an empty list if the table is missing or empty so callers can fall
    back to the hardcoded SEASONS list.
    """
    import json as _json
    try:
        from .db import get_conn  # type: ignore[import]
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT key, label, reason, months, tags FROM seasons ORDER BY sort_order"
            ).fetchall()
    except Exception:
        return []

    if not rows:
        return []

    result: List[Season] = []
    for row in rows:
        try:
            months = _json.loads(row["months"])
            tags = _json.loads(row["tags"])
        except Exception:
            continue
        result.append(Season(key=row["key"], label=row["label"], reason=row["reason"], tags=tags))
    return result


# Month -> Season-index map built once from whatever source is active.
# Rebuilt lazily on first call to _season_for.
_MONTH_TO_SEASON: "dict[int, Season] | None" = None


def _build_month_map(seasons: List[Season]) -> "dict[int, Season]":
    """Build month -> Season mapping from the season list.

    The mapping is derived from SEASONS order + known month ranges.
    When using DB seasons, we store months as JSON on the row so we re-derive
    the map from that. For the fallback SEASONS list we hardcode the same logic.
    """
    # Try to use months metadata from DB rows (stored as JSON on season objects).
    # Fall back to positional mapping for hardcoded SEASONS.
    import json as _json
    try:
        from .db import get_conn  # type: ignore[import]
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT key, months FROM seasons ORDER BY sort_order"
            ).fetchall()
        mapping: dict[int, Season] = {}
        season_by_key = {s.key: s for s in seasons}
        for row in rows:
            try:
                months_list = _json.loads(row["months"])
            except Exception:
                continue
            season = season_by_key.get(row["key"])
            if season is None:
                continue
            for m in months_list:
                mapping[m] = season
        if mapping:
            return mapping
    except Exception:
        pass

    # Hardcoded fallback matching the positional SEASONS list
    return {
        5: seasons[0], 6: seasons[0],
        7: seasons[1], 8: seasons[1],
        9: seasons[2], 10: seasons[2],
        11: seasons[3], 12: seasons[3],
        1: seasons[4], 2: seasons[4], 3: seasons[4], 4: seasons[4],
    }


def _season_for(today: date) -> Season:
    """Map a calendar month to a Season based on the CvSU academic calendar.

    Tries the DB first; falls back to the hardcoded SEASONS list.
    """
    global _MONTH_TO_SEASON

    db_seasons = load_seasons_from_db()
    active_seasons = db_seasons if db_seasons else SEASONS

    if _MONTH_TO_SEASON is None or (db_seasons and len(_MONTH_TO_SEASON) == 0):
        _MONTH_TO_SEASON = _build_month_map(active_seasons)

    m = today.month
    season = _MONTH_TO_SEASON.get(m)
    if season is not None:
        return season

    # Ultimate fallback — last season covers Jan-Apr
    return active_seasons[-1]


def recommend(
    today: Optional[date] = None,
    available_tags: Optional[Iterable[str]] = None,
    max_cards: int = 6,
) -> dict:
    """Return the recommended topic ordering for today.

    `available_tags`, if given, filters out tags that the current intents DB
    doesn't actually serve — so we never recommend a card that would 404.
    """
    today = today or date.today()
    season = _season_for(today)

    tags = list(season.tags)
    if available_tags is not None:
        avail = set(available_tags)
        tags = [t for t in tags if t in avail]

    # Always pad with a stable fallback so the homepage doesn't go empty when
    # the season list and the intents DB drift apart.
    fallback = [
        "admissions_requirements",
        "tuition_fees",
        "courses_offered",
        "scholarship",
        "campus_facilities",
        "contact_info",
    ]
    for t in fallback:
        if t in tags:
            continue
        if available_tags is not None and t not in set(available_tags):
            continue
        tags.append(t)

    return {
        "today": today.isoformat(),
        "season": season.key,
        "label": season.label,
        "reason": season.reason,
        "tags": tags[:max_cards],
    }
