"""Promote coords_override.json into the bundled defaults of both
campusMap.ts (frontend) and campus_places.py (backend), then clear the
override file. Run once after the admin finishes calibrating markers.

Idempotent — running twice with an empty override file does nothing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TS_PATH = ROOT.parent / "SeviWeb" / "app" / "lib" / "campusMap.ts"
PY_PATH = ROOT / "api" / "campus_places.py"
OVERRIDE_PATH = ROOT / "data" / "coords_override.json"


def load_overrides() -> dict[str, dict[str, int]]:
    if not OVERRIDE_PATH.exists():
        return {}
    return json.loads(OVERRIDE_PATH.read_text(encoding="utf-8")) or {}


def update_ts(text: str, coords: dict[str, dict[str, int]]) -> tuple[str, int]:
    """Update `x: NNN, y: NNN,` lines that follow `id: "<place_id>"`."""
    n = 0
    for pid, c in coords.items():
        # Match the building block: id: "<pid>", ... (any chars/newlines) ... x: <num>, y: <num>,
        pattern = re.compile(
            r'(id:\s*"' + re.escape(pid) + r'"[^}]*?)x:\s*\d+,\s*y:\s*\d+,',
            re.DOTALL,
        )
        new_text, count = pattern.subn(
            lambda m, c=c: f"{m.group(1)}x: {c['x']}, y: {c['y']},",
            text,
        )
        if count == 1:
            text = new_text
            n += 1
        elif count == 0:
            print(f"  TS: no match for {pid}")
        else:
            print(f"  TS: {count} matches for {pid} (skipped)")
    return text, n


def update_py(text: str, coords: dict[str, dict[str, int]]) -> tuple[str, int]:
    """Update `"x": NNN, "y": NNN` inside each `"<pid>": { ... }` block."""
    n = 0
    for pid, c in coords.items():
        # _PLACE_METADATA entries are keyed by quoted pid then a dict literal.
        # Match the smallest dict block to keep replacements local.
        pattern = re.compile(
            r'("'
            + re.escape(pid)
            + r'":\s*\{[^{}]*?)"x":\s*\d+,\s*"y":\s*\d+',
            re.DOTALL,
        )
        new_text, count = pattern.subn(
            lambda m, c=c: f"{m.group(1)}\"x\": {c['x']}, \"y\": {c['y']}",
            text,
        )
        if count == 1:
            text = new_text
            n += 1
        elif count == 0:
            print(f"  PY: no match for {pid}")
        else:
            print(f"  PY: {count} matches for {pid} (skipped)")
    return text, n


def main() -> None:
    overrides = load_overrides()
    if not overrides:
        print("No overrides to promote — coords_override.json is empty.")
        return

    print(f"Promoting {len(overrides)} override(s) to bundled defaults...")

    ts_text = TS_PATH.read_text(encoding="utf-8")
    ts_text, ts_n = update_ts(ts_text, overrides)
    TS_PATH.write_text(ts_text, encoding="utf-8")
    print(f"  TS updated: {ts_n}/{len(overrides)}")

    py_text = PY_PATH.read_text(encoding="utf-8")
    py_text, py_n = update_py(py_text, overrides)
    PY_PATH.write_text(py_text, encoding="utf-8")
    print(f"  PY updated: {py_n}/{len(overrides)}")

    # Clear the override file — the bundled defaults now match what was overridden.
    OVERRIDE_PATH.write_text("{}\n", encoding="utf-8")
    print("Override file cleared.")


if __name__ == "__main__":
    main()
