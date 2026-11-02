# JobRadar — Backend

API de veille d'offres d'alternance : FastAPI, PostgreSQL, scoring déterministe, enrichissement IA optionnel et notifications SMTP.

L'interface web est dans le projet séparé `jobradar-frontend`.

## Prérequis
- Docker Desktop + Docker Compose
- (optionnel hors Docker) Python 3.12+

## Démarrage
1. Copier `.env.example` vers `.env`.
2. Modifier au minimum `SECRET_KEY` et, pour les emails, les paramètres SMTP.
3. Lancer : `docker compose up --build`
4. API : http://localhost:8000/docs
5. Santé API : http://localhost:8000/health

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

## Base de données
| Table | Contenu |
|---|---|
| `users` | Utilisateurs |
| `search_profiles` | Critères de recherche |
| `sources` | Plateformes surveillées |
| `offers` | Offres détectées |
| `offer_skills` | Compétences associées |
| `applications` | Suivi des candidatures |
| `notifications` | Historique des emails |
| `collection_logs` | Historique des recherches |

Déduplication : chaque offre reçoit une clé (`deduplication_key`) calculée à partir de son URL canonique (https, hôte sans `www`, sans fragment ni paramètres de suivi type `utm_*` / `trackingId`, paramètres restants triés). Si l'URL est absente ou trop générique, elle est complétée par une empreinte normalisée titre + entreprise + localisation (`app/services/dedup.py`).

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
- `app/scheduler.py` : planification horaire.
- `alembic/` : migrations de schéma.
- `tests/` : tests unitaires et API.

## Limites connues du MVP
- Authentification mono-utilisateur à ajouter avant exposition publique.
- Le connecteur de démonstration est le seul actif immédiatement.
- Les connecteurs de plateformes nécessitent des accès et méthodes de collecte autorisés par chaque fournisseur.
- Prévoir HTTPS, sauvegardes, gestion de secrets, supervision et politique de conservation avant VPS.
