# Development

## Backend

From `backend/`, create a virtual environment, install `requirements.txt`, set `DATABASE_URL`, then run `alembic upgrade head` and `uvicorn app.main:app --reload`. Use SQLite locally; Compose runs PostgreSQL. Alembic owns schema changes. Do not rely on `create_all` at application startup.

Run checks with `python -m compileall -q app tests` and `pytest -q`. Tests use an isolated SQLite database and an unconfigured AI provider so no credentials or network calls are required.

`services.py` holds deterministic text checks, evidence updates, recommendation ranking, and spaced review scheduling. `ai.py` calls OpenAI only from the backend when `OPENAI_API_KEY` is configured. Model suggestions do not create numeric mastery scores. `agents.py` currently provides a small LangGraph dispatcher for the text conversation fallback.

## Frontend

Use Node.js 22+ and pnpm 11.25.0 from `frontend/`. Run `pnpm install --frozen-lockfile`, `pnpm typecheck`, `pnpm lint`, `pnpm build`, then `pnpm dev`. Set `NEXT_PUBLIC_API_URL` for a non-default API address. Never put provider credentials in `NEXT_PUBLIC_*` variables.

`lib/api.ts` adds the current bearer token and surfaces service errors. Protected pages validate the session before showing personal records. Service errors have retry actions where applicable; the UI does not substitute demo analytics.

## Learning signals

The current rubric-free text coach records issue detections, not an English proficiency score. A score remains unset unless a future exercise has a defensible deterministic rubric. The recommendation planner weighs recurring issue counts, time since practice, skill importance, and rubric accuracy only where available; vocabulary reviews add a retention signal. Recommendation responses include their rationale.

Text input does not create a speaking score. Audio capture, transcription, acoustic evaluation, and manager analytics are not implemented.
