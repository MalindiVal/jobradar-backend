# JobRadar — Backend

API de veille d'offres d'alternance : FastAPI, PostgreSQL, n8n pour l'automatisation, scoring déterministe, enrichissement IA optionnel et notifications SMTP.

L'interface web est dans le projet séparé `jobradar-frontend`.

## Prérequis
- Docker Desktop + Docker Compose
- (optionnel hors Docker) Python 3.12+

## Démarrage
1. Copier `.env.example` vers `.env`.
2. Renseigner au minimum `SECRET_KEY`, `JOBRADAR_INTERNAL_KEY` et `N8N_ENCRYPTION_KEY`
   (`python -c "import secrets; print(secrets.token_urlsafe(32))"`), et pour les emails les paramètres SMTP.
3. Lancer : `docker compose up --build`
4. API : http://localhost:8000/docs — santé : http://localhost:8000/health
5. n8n : http://localhost:5678 (créer le compte propriétaire au premier lancement)
6. Vérifier l'ensemble : `powershell -ExecutionPolicy Bypass -File scripts/check-local.ps1`
   (.env, conteneurs, `/health`, `/internal/ping`, `/healthz` de n8n, base n8n, révision Alembic)

État des sources, de Claude et des critères du MVP : voir [docs/mvp-coherence.md](docs/mvp-coherence.md).

| Service | Port | Rôle |
|---|---|---|
| `db` | 5432 | PostgreSQL 16 : base `jobradar` (API) et base `n8n` (données internes de n8n) |
| `api` | 8000 | FastAPI, applique `alembic upgrade head` au démarrage |
| `n8n` | 5678 | Orchestration des collectes ; appelle l'API, jamais la base directement |

La base `n8n` est créée par `docker/postgres/init/01-create-n8n-db.sh`, qui ne s'exécute qu'à l'initialisation d'un volume PostgreSQL vide. Avec un volume créé avant l'ajout de n8n, soit recréer le volume (`docker compose down -v`, perte des données), soit exécuter le script une fois :
`docker compose exec db sh /docker-entrypoint-initdb.d/01-create-n8n-db.sh`

Vérifier depuis n8n l'accès à l'API : nœud HTTP Request `GET {{$env.JOBRADAR_API_URL}}/internal/ping` avec l'en-tête `X-API-Key: {{$env.JOBRADAR_INTERNAL_KEY}}`. Voir `n8n/workflows/README.md` pour l'import/export des workflows.

`CORS_ORIGINS` doit contenir l'URL du frontend (par défaut `http://localhost:3000`).

Le MVP démarre avec un connecteur `demo` qui injecte quelques annonces d'exemple. Les connecteurs LinkedIn, Indeed et Welcome to the Jungle ne contournent aucun contrôle d'accès : ils sont volontairement désactivés tant qu'une API, un flux ou une alerte autorisée n'est pas configuré. France Travail nécessite également des identifiants et autorisations API valides. Ajouter les sources via `app/services/collection/`.

## Configuration
Voir `.env.example`. `AI_ENABLED=false` par défaut : le scoring par règles fonctionne sans fournisseur externe. Pour un fournisseur compatible OpenAI, définir `AI_ENABLED=true`, `AI_API_KEY`, `AI_BASE_URL` et `AI_MODEL`. L'analyse IA est complémentaire et ne remplace pas les règles de filtrage.

SMTP est facultatif. Si `SMTP_HOST` est vide, les notifications restent enregistrées en base mais aucun email n'est envoyé.

## API principale
- `GET /health`
- `GET /api/offers`
- `GET /api/offers/{id}`
- `POST /api/offers` (ajout manuel / ingestion)
- `PATCH /api/offers/{id}` (favori et statut)
- `POST /api/collection/run` (déclenche une collecte)
- `GET /api/collection/runs`
- `GET /api/settings/profile`
- `PUT /api/settings/profile`
- `GET /api/sources`, `PATCH /api/sources/{id}` (activer / désactiver une source)
- `GET /api/applications`, `POST /api/applications`, `GET|PATCH|DELETE /api/applications/{id}` (suivi des candidatures)
- `GET /internal/ping` (réservé à n8n, en-tête `X-API-Key` = `JOBRADAR_INTERNAL_KEY`)

Les offres exposent `application_url` (lien d'origine) ; `source_url` est conservé en lecture et accepté en écriture pour compatibilité.

## Base de données
| Table | Contenu |
|---|---|
| `users` | Utilisateurs |
| `profiles` | Profil professionnel (comparé aux offres par l'analyse IA) |
| `skills` | Référentiel de compétences (unicité insensible à la casse) |
| `profile_skills` | Compétences du profil |
| `search_preferences` | Critères de recherche (mots-clés, lieux, durée, contrat) |
| `job_sources` | Sources des annonces |
| `job_offers` | Annonces collectées |
| `offer_skills` | Compétences extraites d'une annonce |
| `job_analyses` | Résultats de l'analyse IA (score, compétences, points forts/faibles, recommandation) |
| `applications` | Suivi des candidatures |
| `notifications` | Historique des alertes |
| `collection_logs` | Historique des collectes |

Identification d'une offre :
1. contrainte d'unicité `(source_id, external_id)` lorsque la source fournit un identifiant ;
2. sinon, empreinte `deduplication_key` (unique) calculée à partir de l'URL canonique (https, hôte sans `www`, sans fragment ni paramètres de suivi type `utm_*` / `trackingId`, paramètres restants triés), complétée par titre + entreprise + localisation normalisés si l'URL est absente ou trop générique (`app/services/dedup.py`).

`job_offers.analysis_status` (`pending_analysis`, `analyzed`, `analysis_failed`) suit l'analyse IA ; `status` reste le statut de tri côté utilisateur.

## Migrations
Les migrations Alembic sont dans `alembic/`. Au démarrage, l'API applique `alembic upgrade head`. En production, exécuter les migrations comme étape de déploiement dédiée.

## Tests
```bash
python -m pip install -r requirements.txt
pytest
```

## Architecture
- `app/api/` : routes HTTP.
- `app/models/` : modèles SQLAlchemy.
- `app/services/` : collecte, déduplication, scoring, IA et email.
- `app/core/security.py` : protection des routes `/internal` par clé.
- `app/scheduler.py` : planification horaire interne (remplacée par le workflow n8n WF-01 au jalon 4).
- `docker/postgres/init/` : initialisation PostgreSQL (base n8n).
- `n8n/workflows/` : exports JSON des workflows n8n.
- `alembic/` : migrations de schéma.
- `tests/` : tests unitaires et API.

## Limites connues du MVP
- Authentification mono-utilisateur à ajouter avant exposition publique.
- Le connecteur de démonstration est le seul actif immédiatement.
- Les connecteurs de plateformes nécessitent des accès et méthodes de collecte autorisés par chaque fournisseur.
- Prévoir HTTPS, sauvegardes, gestion de secrets, supervision et politique de conservation avant VPS.
