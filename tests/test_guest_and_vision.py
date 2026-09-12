from __future__ import annotations

import pytest

from guest_intelligence.booking_intelligence import BookingIntelligence
from guest_intelligence.crm import GuestCRM
from guest_intelligence.loyalty import LoyaltyEngine
from guest_intelligence.personalization import Personalizer
from guest_intelligence.reporting import GuestReporter
from vision.edge import ingest
from vision.privacy_guard import PrivacyRefuse, guard_frame


def test_uae_and_generic_guest_fixtures():
    crm = GuestCRM()
    markets = {p["market"] for p in crm.list_profiles()}
    assert markets == {"uae", "generic"}


def test_loyalty_and_funnel():
    ev = LoyaltyEngine().evaluate("G-NOOR")
    assert ev["computed_tier"] == "platinum"
    place = BookingIntelligence().place("G-NOOR")
    assert place["stage"] == "stay"


def test_personalization_opt_in():
    noor = Personalizer().recommend("G-NOOR")
    assert noor["marketing_allowed"] is False
    aya = Personalizer().recommend("G-AYA")
    assert aya["marketing_allowed"] is True


def test_reporter_snapshot():
    snap = GuestReporter().snapshot()
    assert snap["guests"] >= 4
    assert "uae" in snap["markets"]


def test_vision_privacy_and_use_cases():
    with pytest.raises(PrivacyRefuse):
        guard_frame({"faces_raw_retained": True, "use_case": "queue"})
    with pytest.raises(PrivacyRefuse):
        guard_frame({"use_case": "vip", "opt_in_vip_ids": [], "faces_raw_retained": False})
    out = ingest("queue_lobby")
    assert out["interpretation"]["action"] == "open_additional_desk"
    vip = ingest("vip_opt_in")
    assert "G-NOOR" in vip["interpretation"]["vip_ids"]
