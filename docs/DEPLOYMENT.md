# Deployment

## Development deployment

Copy `.env.example` to `.env`, replace the database and signing-key placeholders, and run `docker compose up --build`. Compose starts PostgreSQL, applies migrations before the API, and starts the Next.js server. It does not start Redis or a worker.

## Production checklist

- Set `APP_ENV=production` and a randomly generated `SECRET_KEY` of at least 32 characters.
- Use managed PostgreSQL, unique database credentials, TLS, and an external secret manager.
- Set exact HTTPS origins in `CORS_ORIGINS`; configure `NEXT_PUBLIC_API_URL` to the public API URL.
- Set `OPENAI_API_KEY` only on the API service when model feedback is enabled. Keep it out of frontend variables and logs.
- Configure network ingress, backups, alerting, dependency monitoring, and rate limiting at the gateway. The current in-process request limiter is not shared across API replicas.
- Apply Alembic migrations as a release step and confirm `/ready` before sending traffic.
- Review privacy notices and OpenAI API data handling for your organization before enabling AI coaching.

The supplied Compose file is for development, not a production orchestrator. The application does not implement SSO, role-based organization access, privacy-preserving organization analytics, an automated retention schedule, or audio storage controls.
