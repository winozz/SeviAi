"""Date-aware topic recommendations for the DIWA homepage.

The Philippine academic year (and CvSU's in particular) has predictable rhythms
- application/CvSUCAT in summer, enrollment in Aug + Jan, finals + graduation
in Mar-May. When someone opens DIWA we surface the topics that are most
likely to be on their mind right now, before they type.

The mapping is deliberately conservative: the cards still represent topics
that exist in the intents DB, and we fall back to a balanced default when
nothing strongly matches the current month.
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
    Season(
        key="freshman_application",
        label="Applying to CvSU",
        reason="Application & CvSUCAT season — start here.",
        tags=[
            "admissions_requirements",
            "admissions_exam",
            "courses_offered",
            "tuition_fees",
            "scholarship",
            "campus_location",
        ],
    ),
    Season(
        key="enrollment_first_sem",
        label="Enrollment is open",
        reason="It's enrollment week for the 1st semester.",
        tags=[
            "enrollment_procedure",
            "enrollment_schedule",
            "tuition_fees",
            "scholarship",
            "registrar",
            "courses_offered",
        ],
    ),
    Season(
        key="midterms",
        label="Mid-semester",
        reason="Midterm period — academics-heavy questions.",
        tags=[
            "academic_calendar",
            "academic_policies",
            "registrar",
            "campus_facilities",
            "scholarship",
        ],
    ),
    Season(
        key="enrollment_second_sem",
        label="2nd-semester enrollment",
        reason="Second-semester enrollment is happening now.",
        tags=[
            "enrollment_procedure",
            "enrollment_schedule",
            "tuition_fees",
            "registrar",
            "academic_calendar",
        ],
    ),
    Season(
        key="graduation",
        label="Graduation season",
        reason="Finals + graduation period — registrar requests spike.",
        tags=[
            "registrar",
            "academic_calendar",
            "academic_policies",
            "events",
            "contact_info",
        ],
    ),
    Season(
        key="summer",
        label="Summer break",
        reason="Off-cycle — many people are exploring options for next year.",
        tags=[
            "courses_offered",
            "campus_location",
            "campus_facilities",
            "about_cvsu",
            "scholarship",
        ],
    ),
]


def _season_for(today: date) -> Season:
    """Map a calendar month to a Season. PH school year approximations."""
    m = today.month
    if m in (4, 5):
        return SEASONS[0]  # freshman application + CvSUCAT
    if m in (8, 9):
        return SEASONS[1]  # 1st sem enrollment
    if m in (10, 11):
        return SEASONS[2]  # midterms
    if m in (1, 2):
        return SEASONS[3]  # 2nd sem enrollment
    if m == 3:
        return SEASONS[4]  # graduation
    # 6, 7, 12 — summer / off-cycle
    return SEASONS[5]


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
