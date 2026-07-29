# Deployment guide

1. Provision managed PostgreSQL, Redis, an HTTPS reverse proxy, and a secret manager.
2. Set `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, and strict `CORS_ORIGINS`.
3. Build and deploy the API, Celery worker, and web services independently.
4. Run migrations, then seed only non-production environments.
5. Enable observability, backups, key rotation, WAF/rate limiting, and SSO/OIDC before enterprise rollout.

The supplied Compose file is suitable for local development; it is not a production orchestration configuration.
