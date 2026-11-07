# Cohérence avec le MVP JobRadar — état au jalon 1

Référence : cahier des charges technique JobRadar MVP v0.1. Ce document distingue ce qui est
**en place**, ce qui est **prévu** et ce qui **dépend d'un accès externe non obtenu**.

## Organisation des dépôts
Le cahier recommande un monorepo (§11). Le projet garde deux dépôts :
`jobradar-backend` (API, PostgreSQL, n8n, migrations) et `jobradar-frontend` (Next.js).
Le `docker-compose.yml` du backend porte toute l'infrastructure locale ; le frontend se branche
sur `http://localhost:8000` via `CORS_ORIGINS`.

## Composants (§2)
| Composant | État | Remarque |
|---|---|---|
| PostgreSQL 16 | En place | Base `jobradar` (API) + base `n8n` séparée |
| FastAPI | En place | Migrations appliquées au démarrage du conteneur |
| n8n | En place (vide) | Démarre et peut joindre l'API ; aucun workflow encore (WF-01 au jalon 4) |
| Next.js | Dépôt séparé | Pages actuelles à aligner sur le §8 au jalon 6 |
| Claude API | Prévu (jalon 5) | Aucune clé configurée ; le client actuel est générique, compatible OpenAI, désactivé par défaut |

## Collecte toutes les heures (F01)
- Aujourd'hui : l'APScheduler interne lance une collecte toutes les 60 min avec le seul connecteur `demo`.
- Cible : le workflow n8n WF-01 (Schedule Trigger horaire) appellera `POST /internal/offers/upsert`.
  L'APScheduler sera alors désactivé (`SCHEDULER_ENABLED=false`) pour éviter une double collecte.

## Sources ciblées (§4)
Aucun accès externe n'est configuré à ce stade.

| Source | Accès | État |
|---|---|---|
| France Travail | API officielle indiquée comme temporairement non exposée | À vérifier ; aucun identifiant |
| Indeed | API partenaires uniquement, pas d'API de recherche publique | Partenariat à obtenir |
| Welcome to the Jungle | Flux ou intégration autorisée | À vérifier |
| La bonne alternance | Clé API requise pour les routes de lecture | Connecteur de test prévu au jalon 3 ; clé à demander |
| `demo` | Local | Seul connecteur actif (annonce fictive) |

Aucun connecteur ne contournera les conditions d'accès des plateformes (pas de scraping).

## Données (§3) et doublons (F03)
Les 10 tables du §3 existent (migration `0003_mvp_data_model`), plus `offer_skills` et
`collection_logs`. Unicité `(source_id, external_id)` puis empreinte normalisée en repli.
Migration vérifiée sur SQLite et PostgreSQL : montée avec données existantes, schéma identique
aux modèles, descente puis remontée.

## Sécurité (§9)
- Routes `/internal` protégées par `X-API-Key` (`JOBRADAR_INTERNAL_KEY`) ; refusées si la clé est vide.
- Secrets uniquement dans `.env` (non versionné). La future clé Claude restera côté FastAPI.
- Non couvert au jalon 1 : authentification utilisateur (`/auth/login`), HTTPS, sauvegardes.

## Critères de validation du MVP
| Critère | État |
|---|---|
| Collecte automatique toutes les heures | Partiel : APScheduler + `demo` ; n8n au jalon 4 |
| Annonces enregistrées dans PostgreSQL | Oui (connecteur `demo`) |
| Doublons détectés | Oui (tests) |
| Claude analyse les nouvelles annonces | Non (jalon 5) ; table `job_analyses` prête |
| Score explicable | Score par règles avec explication ; score Claude au jalon 5 |
| Dashboard affiche les annonces | Frontend existant, à aligner |
| Liens d'origine consultables | Oui (`application_url`) |
| Erreurs de collecte traçables | Partiel : `collection_logs` ; rapport n8n au jalon 4 |
