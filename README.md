# CommunicateIQ — Adaptive Communication Coach

CommunicateIQ helps professionals practice explaining work, progress, decisions, and impact. The current MVP combines private learner accounts, text-based writing and grammar practice, persisted skill evidence, explainable recommendations, vocabulary review, and progress history.

The product is a learning tool. It does not expose individual learner data to managers, provide employment-performance ratings, or claim that practice causes workplace outcomes.

## Run locally with Docker Compose

1. Copy `.env.example` to `.env` and replace the local placeholders. For production, set a random `SECRET_KEY` with at least 32 characters, a unique database password, `APP_ENV=production`, and HTTPS endpoints.
2. Start the services:

   ```bash
   docker compose up --build
   ```

3. Visit `http://localhost:3000`. FastAPI documentation is at `http://localhost:8000/docs`; liveness and readiness are `/health` and `/ready`.

Compose starts PostgreSQL and runs Alembic migrations before the API. There is no Redis or worker service in the current MVP.

## Local development without Docker

Backend, from `backend/`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///./coach.db"
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend, from `frontend/` (Node.js 22+ and pnpm 11.25.0):

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Set `NEXT_PUBLIC_API_URL` to the API base URL if it differs from `http://localhost:8000/api/v1`.

## Configuration

| Variable | Required | Use |
|---|---|---|
| `DATABASE_URL` | Yes | SQLAlchemy URL, PostgreSQL in Compose or SQLite for local development |
| `SECRET_KEY` | Yes for production | JWT signing secret; production refuses the development default and requires at least 32 characters |
| `APP_ENV` | No | Use `production` to enforce production secret validation |
| `CORS_ORIGINS` | Yes for deployment | Comma-separated allowed browser origins |
| `OPENAI_API_KEY` | No | Server-side writing coach; absent credentials use deterministic text checks |
| `OPENAI_MODEL` | No | OpenAI chat model name; default `gpt-4o-mini` |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose | Local PostgreSQL initialization values |
| `NEXT_PUBLIC_API_URL` | No | Browser-visible API URL; never put secrets in this variable |

The `.env.example` contains placeholders only. Never commit `.env` or real credentials.

## Architecture

- `frontend/`: Next.js App Router, strict TypeScript, Tailwind UI, typed request helper.
- `backend/`: FastAPI API, Pydantic validation, SQLAlchemy models, JWT authentication, Alembic migrations, deterministic learning logic, optional server-side OpenAI writing suggestions.
- `backend/app/services.py`: evidence updates, deterministic text checks, transparent per-skill recommendation scoring, and spaced review intervals.
- `backend/app/ai.py`: optional structured writing feedback. Numeric skill evidence remains deterministic; provider output is clearly identified and can fall back when unavailable.
- `backend/tests/`: API and adaptation checks with SQLite and deterministic behavior.
- `.github/workflows/ci.yml`: backend import/tests and frontend lockfile install, typecheck, lint, and production build.

Skill mastery stores evidence count, recent and historical accuracy, repeated issue count, confidence, practice timestamps, and a bounded trajectory. The planner combines accuracy, observed issues, time since practice, and skill importance, and returns an explanation for each recommendation. The text baseline never infers vocabulary or speaking ability from a writing sample.

## API overview

Protected endpoints use `Authorization: Bearer <JWT>`.

- Authentication: `POST /api/v1/auth/signup`, `POST /api/v1/auth/login`
- Profile and preferences: `GET/PUT /api/v1/profile`
- Text baseline: `POST /api/v1/assessment`
- Personalized plan and next step: `GET /api/v1/lessons/daily`, `GET /api/v1/recommendations`
- Exercises and writing: `POST /api/v1/exercises/submit`, `POST /api/v1/grammar/correct`, `POST /api/v1/writing/coach`
- Vocabulary and analytics: `GET /api/v1/vocabulary`, `POST /api/v1/vocabulary/review`, `GET /api/v1/progress`, `GET /api/v1/dashboard`
- Privacy: `GET /api/v1/data/export`, `DELETE /api/v1/account`

OpenAPI is generated at `/docs`. The checked-in Postman collection is in `docs/Adaptive-English-Coach.postman_collection.json`.

## Verification

From `backend/`:

```bash
python -m compileall -q app
pytest -q
alembic upgrade head
```

From `frontend/`:

```bash
pnpm install --frozen-lockfile
pnpm typecheck
pnpm lint
pnpm build
```

## Current limitations

- Audio capture, transcription, and acoustic evaluation are not implemented. Speaking is never scored from typed text.
- The deterministic checker covers a small set of text conventions. Optional OpenAI suggestions are qualitative and may need human review; numeric exercise evidence does not come from the model.
- No SSO, organization roles, manager analytics, or enterprise identity integration is implemented.
- Account deletion is available in-app. Automated retention expiration, audio retention controls, and a full audit-event system are not yet implemented.
- Theme selection and dark theme, microphone-based simulation, CEFR/IELTS grading, and organization dashboards are not implemented.

See `docs/DEVELOPMENT.md`, `docs/DATABASE.md`, `docs/API.md`, and `docs/DEPLOYMENT.md` for detailed notes.
