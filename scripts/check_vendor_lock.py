#!/usr/bin/env python3
"""Fail CI when blocks/ is edited in place without a VENDOR.lock bump."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "VENDOR.lock"
BLOCKS = ROOT / "blocks"
EXPECTED_COMMIT = "d7cff230453efd273388491e1cbf1d18f3ebefd5"


def digest_dir(path: Path) -> str:
    h = hashlib.sha256()
    files = [p for p in path.rglob("*") if p.is_file() and ".git" not in p.parts]
    for p in sorted(files, key=lambda x: str(x.relative_to(path)).replace("\\", "/")):
        rel = str(p.relative_to(path)).replace("\\", "/")
        h.update(rel.encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def main() -> int:
    if not LOCK_PATH.exists():
        print("VENDOR.lock missing", file=sys.stderr)
        return 1
    if not BLOCKS.is_dir():
        print("blocks/ directory missing", file=sys.stderr)
        return 1

    lock = json.loads(LOCK_PATH.read_text())
    errors: list[str] = []

    if lock.get("commit") != EXPECTED_COMMIT:
        errors.append(
            f"VENDOR.lock commit {lock.get('commit')!r} != required {EXPECTED_COMMIT!r}"
        )

    kits = lock.get("kits") or {}
    required = {
        "hotel_management",
        "event_bus",
        "action_contract",
        "formula_executor_v2",
        "pdf_v2",
        "ocr_v2",
        "hotel_v2",
    }
    missing = required - set(kits)
    if missing:
        errors.append(f"VENDOR.lock missing kits: {sorted(missing)}")

    for name, meta in kits.items():
        path = ROOT / meta["path"]
        if not path.is_dir():
            errors.append(f"kit path missing: {meta['path']}")
            continue
        actual = digest_dir(path)
        if actual != meta.get("digest"):
            errors.append(
                f"blocks/{name} digest drifted ({actual} != {meta.get('digest')}). "
                "Re-vendor and bump VENDOR.lock; do not edit blocks/ in place."
            )

    tree = digest_dir(BLOCKS)
    if tree != lock.get("tree_digest"):
        errors.append(
            f"blocks/ tree_digest drifted ({tree} != {lock.get('tree_digest')}). "
            "CI refuses in-place vendor edits without a lock bump."
        )

    if errors:
        print("VENDOR.lock check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"VENDOR.lock OK — Cerebrum-Blocks@{EXPECTED_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
