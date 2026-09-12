# Cerebrum HotelOps

Pilot-ready hospitality AI: an **ops reasoner** and **guest intelligence**
surface on one normalised event bus. Markets: **UAE + generic** only.

Vendored foundation: Cerebrum-Blocks `@d7cff230453efd273388491e1cbf1d18f3ebefd5`
in `blocks/` (`hotel_management` / `hotel_v2`, `event_bus`, `action_contract`,
formula/pdf/ocr). `VENDOR.lock` pins SHA + kit digests. CI fails if `blocks/`
is edited in place without a lock bump.

## Dual surfaces

| Surface | What it does |
| --- | --- |
| **Ops** | Pre-opening cascade + LRM (M01–M15), engineering inheritance A–D, UAE/generic licensing, two-layer PPM refuse, CMMS/GRMS/POS ingest, vision edge metadata, ActionRegistry audit |
| **Guest** | Booking funnel, loyalty tiers, personalization, CRM taxonomy — synthetic UAE + generic profiles |

Connectors (Opera PMS, Micros Simphony, loyalty LMS, GRMS, Maximo, optional gaming CMS) run **full** connect/fetch/normalise/emit against `fixtures/connectors/`. Live HTTP only when the matching env vars are set.

## Run the fixture pilot

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest                                 # offline, no secrets
uvicorn api.main:app --host 0.0.0.0 --port 43180
```

UI (separate terminal):

```bash
cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 43123
```

Sign in with the local tokens from `.env.example` (`operator-pilot` /
`reviewer-pilot`). Pages: **Ops · Guest · Documents · Actions · Audit**.

Compose (api, workers, postgres+pgvector, redis, web):

```bash
docker compose up --build
```

Optional Jetson overlay: `docker compose -f deploy/docker-compose.jetson.yml --profile jetson up`.

## Markets

Demo fixtures and product markets: **UAE + generic only**. KSA is unsupported
and stripped — `guard_request(market="ksa")` refuses. There is no KSA pack,
branch JSON, or live Saudi property.

Every sheet-derived number carries `evidence_class=B` and a source-check caveat.
Promote to Class A only when the owner uploads brand standards, manning, OS&E
matrices, licence trackers, or PPM records.

## Docs

- `ACCEPTANCE.md` — A01–A05 + guest
- `KNOWN_LIMITATIONS.md` — hardware/secret gates only
- `deploy/secrets_guide.md`
- `domain_kit/licensing/generic_conditional_notes.md` — optional generic outlet notes
