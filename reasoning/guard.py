"""Inbound guard — UAE + generic only. KSA and every other market are refused."""

from __future__ import annotations

from typing import Any, Iterable

# Hard owner constraint: UAE + generic only. No KSA pack, branch, or allowlist.
DEMO_MARKETS = {"uae", "generic", "dubai", "abu_dhabi", "abudhabi", "sharjah", "ajman"}
UNSUPPORTED_MARKETS = {"ksa", "saudi", "saudi_arabia"}
SUPPORTED_MARKETS = DEMO_MARKETS
FORBIDDEN_SOURCES = {"aconex", "procore", "bim", "bim_ifc", "navisworks", "revit"}


class GuardError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "code": self.code, "message": self.message}


def guard_request(
    *,
    market: str | None = None,
    source_system: str | None = None,
    asset_sources: Iterable[str] | None = None,
    construction_pm: bool = False,
    demo_only: bool = False,
) -> None:
    if market:
        code = market.lower()
        if code in UNSUPPORTED_MARKETS:
            raise GuardError(
                "market_unsupported",
                "KSA is unsupported and stripped. Supported markets: UAE and generic only.",
            )
        if demo_only and code not in DEMO_MARKETS:
            raise GuardError(
                "market_not_demo_geography",
                "Pilot demo fixtures are UAE + generic only.",
            )
        if code not in SUPPORTED_MARKETS:
            raise GuardError(
                "market_unsupported",
                "Supported markets: UAE and generic only.",
            )
    if construction_pm:
        raise GuardError(
            "construction_pm_out_of_scope",
            "Aconex/Procore/BIM parse is out of scope. Use CSV/JSON/CMMS ingest.",
        )
    sources = [source_system] if source_system else []
    if asset_sources:
        sources.extend(asset_sources)
    for src in sources:
        if src and src.lower() in FORBIDDEN_SOURCES:
            raise GuardError(
                "construction_pm_out_of_scope",
                f"Source {src!r} is construction-PM/BIM and is refused.",
            )
