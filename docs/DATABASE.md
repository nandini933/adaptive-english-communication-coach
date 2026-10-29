# Database

Alembic migrations target PostgreSQL in Compose and SQLite for local development. Run `alembic upgrade head` from `backend/` before starting the API. Schema is declared in SQLAlchemy models and migration `0001_initial_schema`.

| Table | Purpose |
|---|---|
| `users` | Account identity, password hash, role, industry |
| `learner_profiles` | Private goals and learning preferences |
| `assessments` | Baseline answers, evidence, and caveats |
| `skill_mastery` | Per-user skill evidence, issue frequency, available rubric accuracy, confidence, and trajectory |
| `exercise_attempts` | Submitted prompts, responses, feedback, and observed issues |
| `corrections` | Writing and grammar coach history |
| `vocabulary` | Per-user word review state and next due date |
| `memories` | Structured assessment, practice, conversation, and recall signals |
| `learning_sessions` | Session content and completion metadata |

Every learner query filters by the authenticated user id. `/api/v1/data/export` returns the user's stored learning data; `DELETE /api/v1/account` removes learner-owned records. The current MVP has no scheduled retention cleanup or audio records.

Rubric accuracy and mastery remain unset when an exercise has no defensible deterministic grading rule. Vocabulary recall progress is based on the learner's own review response and is not an external proficiency assessment.
