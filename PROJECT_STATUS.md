# État du socle JobRadar

Référence : cahier des charges technique JobRadar MVP v0.1.

## Jalon 1 — Initialisation technique : fait
- Docker Compose : PostgreSQL 16, API FastAPI, n8n (base PostgreSQL dédiée).
- Modèle de données du §3 : users, profiles, skills, profile_skills, job_offers, job_sources,
  job_analyses, applications, search_preferences, notifications (+ offer_skills, collection_logs).
- Migration Alembic `0003_mvp_data_model` avec reprise des données existantes (testée sur SQLite,
  montée et descente ; pas encore exécutée sur PostgreSQL).
- Clé interne `JOBRADAR_INTERNAL_KEY` et route protégée `GET /internal/ping`.

## Prochaines étapes
- Jalon 2 : `POST /internal/offers/upsert`, `POST /internal/offers/{id}/analyze`,
  `POST /internal/collection-runs`, `/auth/login`, `/dashboard/stats`, `PATCH /offers/{id}/status`.
- Jalon 3 : interface `JobSourceProvider` et connecteur La bonne alternance.
- Jalon 4 : workflow n8n WF-01 (collecte horaire), puis retrait de l'APScheduler interne.
- Jalon 5 : service d'analyse Claude (réponse validée par Pydantic, score à critères explicites),
  en remplacement du client compatible OpenAI actuel.
