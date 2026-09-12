# Known limitations — hardware and secret gates only

HotelOps is pilot-ready offline on fixtures. The items below are **gates**, not
missing product modules.

1. **Live Opera Cloud / OHIP** — requires `OPERA_BASE_URL`, `OPERA_CLIENT_ID`,
   `OPERA_CLIENT_SECRET`. Without them the Opera connector stays on
   `fixtures/connectors/opera/`.
2. **Live Micros Simphony** — requires `MICROS_BASE_URL` + `MICROS_API_KEY`.
3. **Live loyalty LMS / GRMS / Maximo / gaming CMS** — each has matching env
   vars; unset means fixture mode.
4. **Jetson / edge cameras** — `JETSON_GATEWAY_URL` + `JETSON_DEVICE_TOKEN`.
   Vision use cases run on synthetic edge metadata in `fixtures/vision/`.
   Raw frames and face templates are never stored in this repo.
5. **Kimi / Azure LLMs** — optional. Default provider is the deterministic
   fake LLM. Missing secrets produce an honest skip (`LLMSkip`), not a
   fabricated completion.
6. **Auth tokens are fail-closed** — `HOTELOPS_OPERATOR_TOKEN` and
   `HOTELOPS_REVIEWER_TOKEN` have no code defaults. The API refuses to start
   (and refuses all auth) when either is unset/empty. Local/CI must set them
   via env (see `.env.example`). Rotate before any live pilot. HTTP audit
   events are attributed from the authenticated Principal, not client
   `x-actor` / `x-role` headers. Authenticated mutating requests return 503
   if the audit row cannot be persisted.

Not in this product (by owner constraint, not a leftover stub):

- Aconex / Procore / BIM file parse (structured register ingest only)
- Promoting Domain Encoding Sheet rows to Class A without owner artefacts

KSA licensing is stripped. Fixtures and demo geography stay UAE + generic only.
