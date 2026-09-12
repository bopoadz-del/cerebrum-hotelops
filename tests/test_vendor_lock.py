from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vendor_lock_pins_required_commit():
    lock = json.loads((ROOT / "VENDOR.lock").read_text())
    assert lock["commit"] == "d7cff230453efd273388491e1cbf1d18f3ebefd5"
    for kit in (
        "hotel_management",
        "event_bus",
        "action_contract",
        "formula_executor_v2",
        "pdf_v2",
        "ocr_v2",
        "hotel_v2",
    ):
        assert kit in lock["kits"]


def test_vendor_lock_script_green():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_vendor_lock.py")], cwd=ROOT)
    assert proc.returncode == 0
