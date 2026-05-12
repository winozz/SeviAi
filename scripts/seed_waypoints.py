"""Seed data/waypoints_override.json from the (now calibrated) building
positions, so routing uses sensible coords until the admin fine-tunes
each waypoint onto the white roads via the editor.

Strategy:
  - Every wp_X mapped to a building inherits that building's (x, y).
  - "Junction" waypoints (wp_south_row, wp_central, wp_west, wp_north_ring)
    take the centroid of their neighbors' positions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TS_PATH = ROOT.parent / "SeviWeb" / "app" / "lib" / "campusMap.ts"
WAYPOINTS_PATH = ROOT / "data" / "waypoints_override.json"

# Explicit map for waypoints whose name doesn't match a building id 1:1.
EXPLICIT: dict[str, str] = {
    "wp_gate1": "gate_1",
    "wp_gate2": "gate_2",
    "wp_gate3": "gate_3",
    "wp_bahay": "bahay_alumni",
    "wp_research": "research_center",
    "wp_rolle": "rolle_hall",
    "wp_bano": "bano_resort",
    "wp_sci_hs": "sci_hs",
    "wp_star_farm": "star_farm",
    "wp_demo_farm": "demo_farm",
}

# Junctions — no direct building. We'll compute the centroid of neighbors.
JUNCTIONS = {"wp_south_row", "wp_central", "wp_west", "wp_north_ring"}


def parse_buildings(text: str) -> dict[str, dict[str, int]]:
    """Pull (x, y) for each BUILDINGS entry. Buildings always have a `num:`
    field between `id:` and `x:` — that's how we distinguish them from
    waypoint object literals (which share the `id:` shape)."""
    out: dict[str, dict[str, int]] = {}
    pattern = re.compile(
        r'id:\s*"(?P<id>[a-z0-9_]+)"[^}]*?num:\s*\d+[^}]*?x:\s*(?P<x>\d+),\s*y:\s*(?P<y>\d+)',
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        pid = m["id"]
        if pid.startswith("wp_"):
            continue
        out[pid] = {"x": int(m["x"]), "y": int(m["y"])}
    return out


def parse_waypoints(text: str) -> dict[str, list[str]]:
    """Pull neighbors for each waypoint in the WAYPOINTS object literal."""
    out: dict[str, list[str]] = {}
    # Match: wp_xxx: { id: "wp_xxx", x: N, y: N, neighbors: [...] }
    pattern = re.compile(
        r'(?P<id>wp_[a-z0-9_]+):\s*\{[^}]*?neighbors:\s*\[(?P<n>[^\]]*)\]',
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        raw = m["n"]
        neighbors = re.findall(r'"(wp_[a-z0-9_]+)"', raw)
        out[m["id"]] = neighbors
    return out


def building_for_waypoint(wp_id: str, buildings: dict[str, dict[str, int]]) -> str | None:
    if wp_id in EXPLICIT:
        b = EXPLICIT[wp_id]
        return b if b in buildings else None
    # Drop wp_ prefix and look up directly.
    bid = wp_id[len("wp_") :]
    if bid in buildings:
        return bid
    return None


def main() -> None:
    ts = TS_PATH.read_text(encoding="utf-8")
    buildings = parse_buildings(ts)
    waypoints = parse_waypoints(ts)

    print(f"Parsed {len(buildings)} buildings, {len(waypoints)} waypoints.")

    # Pass 1: direct building mappings.
    coords: dict[str, dict[str, int]] = {}
    unresolved: list[str] = []
    for wp_id, neighbors in waypoints.items():
        b = building_for_waypoint(wp_id, buildings)
        if b is not None:
            coords[wp_id] = buildings[b]
        else:
            unresolved.append(wp_id)

    # Pass 2: junctions / unresolved — centroid of resolved neighbors.
    # Iterate up to twice in case a junction's only resolved neighbor is
    # another junction (rare but possible).
    for _ in range(3):
        still: list[str] = []
        for wp_id in unresolved:
            ns = waypoints.get(wp_id, [])
            pts = [coords[n] for n in ns if n in coords]
            if not pts:
                still.append(wp_id)
                continue
            cx = sum(p["x"] for p in pts) // len(pts)
            cy = sum(p["y"] for p in pts) // len(pts)
            coords[wp_id] = {"x": cx, "y": cy}
        unresolved = still
        if not unresolved:
            break

    if unresolved:
        print(f"  Still unresolved (no neighbor coords): {unresolved}")

    # Additive merge: keep any existing overrides (manual admin edits)
    # and only fill in waypoints that are currently missing. Pass
    # SEED_OVERWRITE=1 in the env to ignore existing entries.
    import os
    existing: dict[str, dict[str, int]] = {}
    if WAYPOINTS_PATH.exists() and not os.environ.get("SEED_OVERWRITE"):
        try:
            existing = json.loads(WAYPOINTS_PATH.read_text(encoding="utf-8")) or {}
        except json.JSONDecodeError:
            existing = {}
    added = 0
    for wid, c in coords.items():
        if wid in existing:
            continue
        existing[wid] = c
        added += 1
    WAYPOINTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WAYPOINTS_PATH.write_text(
        json.dumps(existing, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {len(existing)} waypoint(s) total to {WAYPOINTS_PATH.name} "
        f"({added} newly seeded, {len(existing) - added} preserved)."
    )


if __name__ == "__main__":
    main()
