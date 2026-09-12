# Generic market-conditional notes

These are **optional notes**, not a live market pack and not a country branch.

Pilot markets remain **UAE + generic**. Do not add a country-specific licensing
tree for any other jurisdiction.

## Outlet-type conditions (generic only)

When a property asks for a **generic** pack, the reasoner may surface these as
optional, market-conditional questions. They are never auto-required.

- **Alcohol service** — some destinations require a separate liquor / tourism
  add-on. Treat as optional; do not assume it is permitted or forbidden.
- **Shisha / hookah lounge** — some municipalities license this as a distinct
  smoking-outlet use. Optional note only.
- **Religious-affairs / public-morality review** — a few jurisdictions route
  entertainment through a cultural or religious-affairs office. Record as an
  optional generic branch question (`entertainment_review_required?`), never as
  a named national pack.

If the operator does not answer, the verdict is **UNPROVABLE** for that
optional row — not FAIL, and not a silent PASS.

## Never do

- Do not create `branches/ksa.json` or any Saudi-only MOI / Islamic Affairs /
  shisha rows.
- Do not label utilities, ISP lead time, star classification, or CCTV as
  country-specific; those are general hospitality Class B patterns already
  mapped into `generic_template.json` and `uae/`.
