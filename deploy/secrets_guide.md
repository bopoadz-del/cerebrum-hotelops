# Secrets guide

Nothing in `.env.example` is a production secret. Put live values in the
host environment or the Cloud Agents / Render dashboard.

| Variable | Required for offline pilot | Live gate |
| --- | --- | --- |
| `HOTELOPS_OPERATOR_TOKEN` | yes — set in env; no code default | rotate before live pilot |
| `HOTELOPS_REVIEWER_TOKEN` | yes — set in env; no code default | rotate before live pilot |
| `HOTELOPS_CORS_ORIGINS` | local Vite origins if unset | explicit browser origins; never `*` |
| `DATABASE_URL` | sqlite default / compose postgres | managed Postgres |
| `KIMI_API_KEY` | no | optional LLM |
| `AZURE_OPENAI_*` | no | optional LLM |
| `OPERA_*` / `MICROS_*` / `LOYALTY_LMS_*` / `GRMS_*` / `MAXIMO_*` | no | live connectors |
| `JETSON_*` | no | edge cameras |

If a live connector/LLM secret is missing, HotelOps stays on fixtures and the fake LLM.
That skip is honest — it does not invent Opera/Micros payloads.

Auth tokens are fail-closed: if `HOTELOPS_OPERATOR_TOKEN` or
`HOTELOPS_REVIEWER_TOKEN` is unset or empty, the API refuses to start and
refuses all bearer auth. Pytest/CI must export them (see `.env.example`).
Do not rely on strings baked into `Settings`.
