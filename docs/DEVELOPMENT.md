# Developer guide

The FastAPI API uses routers-in-one-module for an intentionally compact foundation; move endpoints into feature routers as the team grows. `agents.py` uses a LangGraph supervisor to dispatch Assessment, Grammar, Vocabulary, Writing, Conversation, and Learning Planner specialists. `services.py` is the deterministic agent fallback and domain boundary. Replace its provider implementation with OpenAI Responses calls behind the same functions; validate every response with Pydantic before persistence.

The supervisor concept is represented by the endpoint workflow: request → profile and memory context → specialist function → validated output → memory write. In production, model this explicitly with LangGraph nodes for Assessment, Grammar, Vocabulary, Writing, Conversation, Planner, Feedback, Memory, and Analytics. Keep all model calls server-side and make writes idempotent.

Run tests: `cd backend; pytest`. Use migrations (Alembic) before deploying beyond the starter SQLite mode.
