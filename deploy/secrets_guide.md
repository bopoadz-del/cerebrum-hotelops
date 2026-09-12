# Secrets guide

Nothing in `.env.example` is a production secret. Put live values in the
host environment or the Cloud Agents / Render dashboard.

| Variable | Required for offline pilot | Live gate |
| --- | --- | --- |
| `HOTELOPS_OPERATOR_TOKEN` | yes (local default) | rotate in production |
| `HOTELOPS_REVIEWER_TOKEN` | yes (local default) | rotate in production |
| `DATABASE_URL` | sqlite default / compose postgres | managed Postgres |
| `KIMI_API_KEY` | no | optional LLM |
| `AZURE_OPENAI_*` | no | optional LLM |
| `OPERA_*` / `MICROS_*` / `LOYALTY_LMS_*` / `GRMS_*` / `MAXIMO_*` | no | live connectors |
| `JETSON_*` | no | edge cameras |

If a live secret is missing, HotelOps stays on fixtures and the fake LLM.
That skip is honest — it does not invent Opera/Micros payloads.
