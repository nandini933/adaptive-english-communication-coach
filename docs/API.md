# API

OpenAPI is served at `/docs` and `/openapi.json`. Protected routes use `Authorization: Bearer <JWT>`.

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/v1/auth/signup` | Register an account and return a token |
| `POST` | `/api/v1/auth/login` | Authenticate and return a token |
| `GET`, `PUT` | `/api/v1/profile` | Read profile and update allowed learning preferences |
| `POST` | `/api/v1/assessment` | Store an optional baseline text sample and observable text evidence |
| `GET` | `/api/v1/lessons/daily` | Return next practice with a recommendation rationale |
| `POST` | `/api/v1/exercises/submit` | Persist a text practice attempt and detected issues |
| `POST` | `/api/v1/grammar/correct` | Return grammar-focused text coaching |
| `POST` | `/api/v1/writing/coach` | Return selected writing mode feedback |
| `POST` | `/api/v1/conversation` | Return qualitative, text-only workplace practice feedback |
| `GET` | `/api/v1/recommendations` | Return the next learning action and reason |
| `GET` | `/api/v1/vocabulary` | Return saved reviews and due count |
| `POST` | `/api/v1/vocabulary/review` | Save recall result and schedule next review |
| `GET` | `/api/v1/dashboard` | Return counts and recorded learner evidence |
| `GET` | `/api/v1/progress` | Return per-skill evidence trajectory and attempts |
| `GET` | `/api/v1/data/export` | Export profile, history, vocabulary, and memory |
| `DELETE` | `/api/v1/account` | Delete account and learner-owned records |
| `GET` | `/health`, `/ready` | Liveness and database readiness |

The Postman collection at `Adaptive-English-Coach.postman_collection.json` uses collection variables for base URL, email, password, and token. Register or set credentials, then log in to populate the token variable.

The deterministic text checker detects a small set of conventions. Its issue counts are not a proficiency score. Speaking is never inferred from text. OpenAI writing suggestions are optional, server-side, qualitative, and stored with the submission.
