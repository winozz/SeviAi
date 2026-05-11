"""Canonical campus place data for the CvSU Don Severino delas Alas Campus (Indang).

Single source of truth for the chatbot's map feature. Both `app.py` (root) and
`api/app.py` import from this module so the 48 locations from the official
campus map (Matayuyon Crop Science Society, 2026) stay in lockstep across
entry points.

Pixel coordinates (x, y) are in the campus image's 2000 x 2000 reference frame
and match `SeviWeb/app/lib/campusMap.ts`. Keep the two files in sync when
moving markers.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Models exposed by the API
# ---------------------------------------------------------------------------

class MapData(BaseModel):
    place_id: str  # key into the campus map (matches frontend Building.id)
    label: str     # human-readable building/area name


class PlaceMeta(BaseModel):
    place_id: str
    label: str
    num: int                          # legend number on the official map (1..48)
    short: str
    full: str
    walk_minutes_from_gate: int
    direction_from_gate: str
    # Pin center on the 2000 x 2000 campus image. None for the full-campus view.
    x: Optional[int] = None
    y: Optional[int] = None


# ---------------------------------------------------------------------------
# Layout reference (must match SeviWeb/app/lib/campusMap.ts)
# ---------------------------------------------------------------------------

_GATE = {"x": 470, "y": 1810}  # Gate 1 — Main Gate
_CAMPUS_VIEWBOX = {"width": 2000, "height": 2000}


# ---------------------------------------------------------------------------
# Place metadata — 48 numbered locations + a virtual "main" full-campus view
# ---------------------------------------------------------------------------
# Each entry: place_id -> {num, short, full, walk_minutes_from_gate,
# direction_from_gate, x, y}
#
# `num` is the legend number on the official campus map. `direction_from_gate`
# is a concise one-line direction; richer step-by-step text lives on the
# frontend (`campusMap.ts`).

_PLACE_METADATA: Dict[str, Dict[str, Any]] = {
    "main": {"num": 0, "short": "Campus", "full": "CvSU Don Severino delas Alas Campus – Indang",
             "walk_minutes_from_gate": 0,
             "direction_from_gate": "Enter via Gate 1 (Main Gate). The campus has 48 numbered locations across 10+ colleges, dormitories, an oval, a library, and farms.",
             "x": None, "y": None},

    "plaza":          {"num": 1,  "short": "Plaza",         "full": "University Plaza (Laya't Diwa)",
                       "walk_minutes_from_gate": 1, "direction_from_gate": "Just inside Gate 1 on the south entrance.",
                       "x": 380,  "y": 1830},
    "gate_1":         {"num": 2,  "short": "Gate 1",        "full": "Gate 1 (Main Gate)",
                       "walk_minutes_from_gate": 0, "direction_from_gate": "Gate 1 is the southern main entrance — you're here.",
                       "x": 470,  "y": 1810},
    "softball":       {"num": 3,  "short": "Softball",      "full": "Softball Field",
                       "walk_minutes_from_gate": 2, "direction_from_gate": "From Gate 1, head west along the southern boundary.",
                       "x": 290,  "y": 1640},
    "intl_house":     {"num": 4,  "short": "Intl House",    "full": "International House — Marketing",
                       "walk_minutes_from_gate": 1, "direction_from_gate": "From Gate 1, walk east a short distance.",
                       "x": 540,  "y": 1810},
    "bleachers":      {"num": 5,  "short": "Bleachers",     "full": "Bleachers",
                       "walk_minutes_from_gate": 2, "direction_from_gate": "Walk north from Gate 1 toward the University Oval.",
                       "x": 610,  "y": 1750},
    "open_court":     {"num": 6,  "short": "Open Court",    "full": "Open Court",
                       "walk_minutes_from_gate": 3, "direction_from_gate": "Walk north from Gate 1; the open court is east of the oval.",
                       "x": 650,  "y": 1640},
    "oval":           {"num": 7,  "short": "Oval",          "full": "University Oval — Grandstand",
                       "walk_minutes_from_gate": 4, "direction_from_gate": "Walk straight north from Gate 1; the oval is the central track.",
                       "x": 570,  "y": 1430},
    "mall":           {"num": 8,  "short": "Mall",          "full": "University Mall",
                       "walk_minutes_from_gate": 2, "direction_from_gate": "From Gate 1, walk east along the southern row.",
                       "x": 700,  "y": 1810},
    "osas":           {"num": 9,  "short": "OSAS",          "full": "Office of Student Affairs and Services (OSAS) — University Registrar",
                       "walk_minutes_from_gate": 4, "direction_from_gate": "From Gate 1, walk north past the oval; OSAS / Registrar is on the east side.",
                       "x": 820,  "y": 1640},
    "gym":            {"num": 10, "short": "Gymnasium",     "full": "College of Sports and Physical Education and Recreation — University Gymnasium",
                       "walk_minutes_from_gate": 4, "direction_from_gate": "Walk north past the bleachers and open court; the gymnasium is on the east side.",
                       "x": 810,  "y": 1700},
    "boys_dorm":      {"num": 11, "short": "Boys Dorm",     "full": "Boy's Dormitory",
                       "walk_minutes_from_gate": 3, "direction_from_gate": "From Gate 1, walk east past the University Mall.",
                       "x": 900,  "y": 1810},
    "bahay_alumni":   {"num": 12, "short": "Bahay Alumni",  "full": "Bahay Alumni",
                       "walk_minutes_from_gate": 4, "direction_from_gate": "Walk east past the mall and gymnasium; near the east dorm cluster.",
                       "x": 960,  "y": 1740},
    "girls_dorm":     {"num": 13, "short": "Girls Dorm",    "full": "Girl's Dormitory",
                       "walk_minutes_from_gate": 4, "direction_from_gate": "Walk east along the southern row, past Bahay Alumni.",
                       "x": 1080, "y": 1810},
    "ncrdec":         {"num": 14, "short": "NCRDEC",        "full": "National Coffee Research, Development, and Extension Center (NCRDEC)",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Walk east to the far edge of campus; NCRDEC is in the eastern strip.",
                       "x": 1240, "y": 1660},
    "demo_farm":      {"num": 15, "short": "Demo Farm",     "full": "Technology Demonstration Farm",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Walk northeast past the gymnasium toward the agri zone.",
                       "x": 1180, "y": 1530},
    "processing":     {"num": 16, "short": "Processing",    "full": "Fruits and Vegetable Processing Center",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Northeast section, next to the demo farm.",
                       "x": 1100, "y": 1530},
    "cafenr":         {"num": 17, "short": "CAFENR",        "full": "College of Agriculture, Food, Environment, and Natural Resources (CAFENR)",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Walk north past Admin and the oval; CAFENR is in the central-east area.",
                       "x": 1010, "y": 1370},
    "dcs":            {"num": 18, "short": "DCS",           "full": "Department of Crop Science (DCS)",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Beside CAFENR in the central-east cluster.",
                       "x": 950,  "y": 1370},
    "cemds":          {"num": 19, "short": "CEMDS",         "full": "College of Economics, Management, and Development Studies (CEMDS)",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Walk north past Admin and CAFENR; CEMDS is north-central, east side.",
                       "x": 1070, "y": 1240},
    "research_center":{"num": 20, "short": "Research",      "full": "Research Center",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Just north of CEMDS in the north-central area.",
                       "x": 1030, "y": 1170},
    "cthm":           {"num": 21, "short": "CTHM",          "full": "College of Tourism and Hospitality Management (CTHM)",
                       "walk_minutes_from_gate": 7, "direction_from_gate": "Walk north along the eastern road past CEMDS.",
                       "x": 1020, "y": 1040},
    "cas":            {"num": 22, "short": "CAS",           "full": "College of Arts and Sciences (CAS)",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Walk north from Gate 1 past Admin and the oval; CAS is in the upper-central cluster.",
                       "x": 840,  "y": 1040},
    "old_cemds":      {"num": 23, "short": "Old CEMDS",     "full": "Old CEMDS Building",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Walk north from Gate 1 past Admin; the Old CEMDS is west of CAS.",
                       "x": 640,  "y": 1040},
    "admin":          {"num": 24, "short": "Admin",         "full": "Administration Building — University Cashier",
                       "walk_minutes_from_gate": 3, "direction_from_gate": "Walk straight north from Gate 1 — the Administration Building is the first major structure.",
                       "x": 430,  "y": 1170},
    "ceit":           {"num": 25, "short": "CEIT",          "full": "College of Engineering and Information Technology (CEIT)",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Walk north from Gate 1 then bear left past Admin; CEIT is near Gate 2.",
                       "x": 310,  "y": 1100},
    "child_dev":      {"num": 26, "short": "Child Dev",     "full": "Child Development Center",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Enter via Gate 2 on the west, or walk north-west from Gate 1.",
                       "x": 260,  "y": 1040},
    "gate_2":         {"num": 27, "short": "Gate 2",        "full": "Gate 2",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Gate 2 is the western entrance, on the side of CEIT and the Chapel.",
                       "x": 220,  "y": 1130},
    "chapel":         {"num": 28, "short": "Chapel",        "full": "University Chapel",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Enter via Gate 2 or walk west from the central road past Admin.",
                       "x": 240,  "y": 1240},
    "ccj":            {"num": 29, "short": "CCJ",           "full": "College of Criminal Justice (CCJ)",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "On the western edge, south of the Chapel.",
                       "x": 220,  "y": 1320},
    "clinic":         {"num": 30, "short": "Clinic",        "full": "University Clinic (Infirmary)",
                       "walk_minutes_from_gate": 4, "direction_from_gate": "Walk west from Gate 1 along the southern road, then turn north.",
                       "x": 250,  "y": 1430},
    "sci_hs":         {"num": 31, "short": "Sci HS",        "full": "Science Highschool",
                       "walk_minutes_from_gate": 4, "direction_from_gate": "Walk north from Gate 1, then west of the Administration Building.",
                       "x": 370,  "y": 1320},
    "quadrangle":     {"num": 32, "short": "Quad",          "full": "Quadrangle",
                       "walk_minutes_from_gate": 3, "direction_from_gate": "The open area just south of the Administration Building.",
                       "x": 420,  "y": 1310},
    "coed":           {"num": 33, "short": "CEd",           "full": "College of Education (CED)",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Walk north past Admin; CED is in the west-central cluster near CEIT.",
                       "x": 360,  "y": 1170},
    "hostel":         {"num": 34, "short": "Hostel",        "full": "Hostel Tropicana",
                       "walk_minutes_from_gate": 8, "direction_from_gate": "Walk north past CEMDS and the Research Center; in the northeast cluster.",
                       "x": 1130, "y": 970},
    "agri_eco":       {"num": 35, "short": "Agri-Eco",      "full": "CvSU Agri-Eco Park",
                       "walk_minutes_from_gate": 9, "direction_from_gate": "Walk north along the eastern road past CTHM and the hostel.",
                       "x": 1150, "y": 880},
    "saluysoy":       {"num": 36, "short": "Saluysoy",      "full": "Saluysoy",
                       "walk_minutes_from_gate": 9, "direction_from_gate": "Walk north past CTHM into the upper-east section.",
                       "x": 1080, "y": 800},
    "bano_resort":    {"num": 37, "short": "Baño Resort",   "full": "Baño De Señora Resort",
                       "walk_minutes_from_gate": 10, "direction_from_gate": "Walk north all the way past CTHM and the Agri-Eco area; the resort is at the northeast edge.",
                       "x": 1130, "y": 720},
    "icon":           {"num": 38, "short": "ICON",          "full": "International Convention Center (ICON)",
                       "walk_minutes_from_gate": 9, "direction_from_gate": "Walk far north past CAS and the library cluster.",
                       "x": 750,  "y": 800},
    "con":            {"num": 39, "short": "CON",           "full": "College of Nursing (CON)",
                       "walk_minutes_from_gate": 8, "direction_from_gate": "Walk north past Admin and the library; CON is in the north-central area near CAS.",
                       "x": 820,  "y": 970},
    "cvmbs":          {"num": 40, "short": "CVMBS",         "full": "College of Veterinary Medicine and Biological Sciences (CVMBS)",
                       "walk_minutes_from_gate": 11, "direction_from_gate": "Walk far north past CAS, the library, and ICON; CVMBS is in the upper-north section.",
                       "x": 760,  "y": 600},
    "star_farm":      {"num": 41, "short": "Star Farm",     "full": "CvSU Star Farm",
                       "walk_minutes_from_gate": 13, "direction_from_gate": "All the way north past CVMBS — the Star Farm is at the far northern tip.",
                       "x": 890,  "y": 470},
    "das":            {"num": 42, "short": "DAS",           "full": "Department of Animal Science (DAS)",
                       "walk_minutes_from_gate": 11, "direction_from_gate": "Walk far north past CTHM and the Agri-Eco area; DAS is east of CVMBS.",
                       "x": 990,  "y": 600},
    "gate_3":         {"num": 43, "short": "Gate 3",        "full": "Gate 3",
                       "walk_minutes_from_gate": 2, "direction_from_gate": "Gate 3 is the third entrance, on the south side near the dorm row.",
                       "x": 740,  "y": 1810},
    "lagoon":         {"num": 44, "short": "Lagoon",        "full": "Lagoon",
                       "walk_minutes_from_gate": 9, "direction_from_gate": "Walk north past Admin, the library, and CAS — the lagoon is the water feature in the north-central area.",
                       "x": 870,  "y": 800},
    "library":        {"num": 45, "short": "Library",       "full": "Ladislao N. Diwa Memorial Library",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Walk north from Gate 1 past the Administration Building and CAFENR; the library is central.",
                       "x": 920,  "y": 1170},
    "gender_dev":     {"num": 46, "short": "GAD",           "full": "Gender and Development Research Center",
                       "walk_minutes_from_gate": 6, "direction_from_gate": "Walk north past Admin and the library; the GAD Research Center is in the central area near CAS.",
                       "x": 810,  "y": 1090},
    "grad":           {"num": 47, "short": "Grad School",   "full": "Graduate School",
                       "walk_minutes_from_gate": 5, "direction_from_gate": "Walk north from Gate 1 past Admin; Graduate School is in the central area near the library.",
                       "x": 700,  "y": 1130},
    "rolle_hall":     {"num": 48, "short": "Rolle Hall",    "full": "S.M Rolle Hall",
                       "walk_minutes_from_gate": 8, "direction_from_gate": "Walk north past CAS into the upper-central area.",
                       "x": 620,  "y": 800},
}

_PLACE_LABELS: Dict[str, str] = {pid: meta["full"] for pid, meta in _PLACE_METADATA.items()}


# ---------------------------------------------------------------------------
# Keyword aliases per place. Ordering matters — more specific (longer, unique)
# names come first so they win over generic substrings. Matches use whole-word
# boundaries (see `_matches_term`), which prevents "cas" from triggering on
# "campus" or "ced" from triggering on "exceeded". Includes Tagalog aliases.
# ---------------------------------------------------------------------------

_PLACE_KEYWORDS: List[Tuple[str, List[str]]] = [
    # Unique multi-word phrases (longest, safest matches first)
    ("ncrdec",          ["ncrdec", "national coffee research", "coffee research", "extension center"]),
    ("intl_house",      ["international house", "marketing house"]),
    ("processing",      ["fruits and vegetable processing", "vegetable processing", "processing center", "fruits and vegetable"]),
    ("demo_farm",       ["technology demonstration farm", "demonstration farm", "demo farm", "tech demo"]),
    ("gender_dev",      ["gender and development", "gender development", "gad research", "gad center"]),
    ("agri_eco",        ["agri-eco", "agri eco", "eco park", "agri-eco park"]),
    ("bano_resort",     ["baño de señora", "bano de senora", "baño resort", "bano resort", "señora resort"]),
    ("research_center", ["research center"]),
    ("old_cemds",       ["old cemds"]),
    ("star_farm",       ["star farm", "cvsu star farm"]),
    ("bahay_alumni",    ["bahay alumni", "alumni house"]),
    ("hostel",          ["hostel tropicana", "tropicana"]),
    ("child_dev",       ["child development", "child dev", "daycare", "day care"]),
    ("rolle_hall",      ["rolle hall", "s.m rolle", "sm rolle", "rolle"]),
    ("sci_hs",          ["science highschool", "science high school", "high school", "shs"]),
    ("intl_house",      ["intl house"]),

    # Unique college abbreviations
    ("ceit",            ["ceit", "engineering", "information technology", "computer science", "computer engineering", "electronics engineering"]),
    ("cafenr",          ["cafenr", "agriculture", "food technology", "environment and natural", "natural resources", "agri"]),
    ("cemds",           ["cemds", "economics", "management studies", "development studies", "business administration", "accountancy"]),
    ("coed",            ["coed", "ced", "college of education", "ceduc", "teacher education", "education building"]),
    ("cvmbs",           ["cvmbs", "veterinary", "vet med", "biological sciences"]),
    ("cthm",            ["cthm", "tourism", "hospitality"]),
    ("cas",             ["cas", "arts and sciences", "arts & sciences", "liberal arts"]),
    ("ccj",             ["ccj", "criminal justice"]),
    ("con",             ["con", "nursing", "college of nursing"]),
    ("dcs",             ["dcs", "crop science", "department of crop"]),
    ("das",             ["das", "animal science", "department of animal"]),
    ("osas",            ["osas", "student affairs", "registrar", "university registrar"]),
    ("icon",            ["icon", "convention center", "international convention"]),
    ("grad",            ["graduate school", "grad school", "masteral", "doctoral", "post-graduate", "postgraduate"]),

    # Singular landmarks / facilities
    ("library",         ["library", "aklatan", "diwa library", "ladislao", "ladislao diwa"]),
    ("admin",           ["admin", "administration", "administration building", "admin building", "cashier", "university cashier", "pangasiwaan"]),
    ("chapel",          ["chapel", "simbahan", "kapilya", "university church"]),
    ("gym",             ["gym", "gymnasium", "himnasyo", "sports complex", "sports and physical"]),
    ("mall",            ["mall", "university mall", "canteen", "cafeteria", "kantina", "food court"]),
    ("clinic",          ["clinic", "infirmary", "university clinic", "ospital"]),
    ("oval",            ["oval", "track", "grandstand", "university oval"]),
    ("open_court",      ["open court", "basketball court"]),
    ("bleachers",       ["bleachers"]),
    ("softball",        ["softball", "softball field"]),
    ("quadrangle",      ["quadrangle", "quad"]),
    ("plaza",           ["plaza", "laya't diwa", "laya t diwa", "university plaza"]),
    ("lagoon",          ["lagoon"]),
    ("saluysoy",        ["saluysoy"]),
    ("boys_dorm",       ["boys dorm", "boy's dorm", "boy dormitory", "boys dormitory", "boy's dormitory"]),
    ("girls_dorm",      ["girls dorm", "girl's dorm", "girl dormitory", "girls dormitory", "girl's dormitory"]),

    # Gates
    ("gate_1",          ["gate 1", "main gate", "entrance"]),
    ("gate_2",          ["gate 2"]),
    ("gate_3",          ["gate 3"]),

    # Catch-all for general CvSU queries — must come last
    ("main",            ["cvsu", "main campus", "campus map", "the campus", "indang campus", "pamantasan", "unibersidad", "don severino"]),
]


_LOCATION_KEYWORDS = {
    "where", "location", "direction", "directions",
    "how to get", "how to find", "get to", "go to", "locate", "find",
    "building", "place", "address",
    "saan", "nasaan", "paano pumunta", "paano makakapunta",
    "papunta", "papuntang", "pupunta", "pupuntang", "pumunta",
}


_TERM_REGEX_CACHE: Dict[str, "re.Pattern[str]"] = {}


def _matches_term(msg: str, term: str) -> bool:
    """Whole-word match: \\bterm\\b against the lowercased message.

    Phrases (e.g. "old cemds", "paano pumunta") work because the word
    boundaries are anchored only at the start and end of the escaped term.
    """
    pat = _TERM_REGEX_CACHE.get(term)
    if pat is None:
        pat = re.compile(r"\b" + re.escape(term) + r"\b")
        _TERM_REGEX_CACHE[term] = pat
    return pat.search(msg) is not None


def resolve_map_data(message: str, intent: str) -> Optional[MapData]:
    """Return MapData for location-related queries; covers the Indang main campus."""
    msg = message.lower()
    has_location_kw = any(_matches_term(msg, kw) for kw in _LOCATION_KEYWORDS)

    if intent == "campus_location":
        for pid, keywords in _PLACE_KEYWORDS:
            if any(_matches_term(msg, kw) for kw in keywords):
                return MapData(place_id=pid, label=_PLACE_LABELS[pid])
        return MapData(place_id="main", label=_PLACE_LABELS["main"])

    if has_location_kw:
        for pid, keywords in _PLACE_KEYWORDS:
            if any(_matches_term(msg, kw) for kw in keywords):
                return MapData(place_id=pid, label=_PLACE_LABELS[pid])

    return None


def build_place_meta(place_id: str) -> PlaceMeta:
    meta = _PLACE_METADATA[place_id]
    return PlaceMeta(
        place_id=place_id,
        label=_PLACE_LABELS[place_id],
        num=meta["num"],
        short=meta["short"],
        full=meta["full"],
        walk_minutes_from_gate=meta["walk_minutes_from_gate"],
        direction_from_gate=meta["direction_from_gate"],
        x=meta["x"], y=meta["y"],
    )


def campus_map_payload() -> Dict[str, Any]:
    return {
        "gate": _GATE,
        "viewbox": _CAMPUS_VIEWBOX,
        "places": [build_place_meta(pid) for pid in _PLACE_METADATA.keys()],
    }


def has_place(place_id: str) -> bool:
    return place_id in _PLACE_METADATA


# Re-exported for convenience
__all__ = [
    "MapData", "PlaceMeta",
    "resolve_map_data", "build_place_meta", "campus_map_payload", "has_place",
]
