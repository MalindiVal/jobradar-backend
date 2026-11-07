# Workflows n8n

Exports JSON des workflows JobRadar, versionnés avec le backend.

Le dossier est monté dans le conteneur sous `/workflows`.

- Importer tous les workflows du dossier :
  `docker compose exec n8n n8n import:workflow --separate --input=/workflows`
- Exporter les workflows après modification dans l'interface :
  `docker compose exec n8n n8n export:workflow --all --separate --output=/workflows`

Variables disponibles dans les nœuds (expressions `{{$env.…}}`) :

| Variable | Valeur |
|---|---|
| `JOBRADAR_API_URL` | `http://api:8000` (réseau Docker) |
| `JOBRADAR_INTERNAL_KEY` | Clé à envoyer dans l'en-tête `X-API-Key` des routes `/internal` |

À venir (jalon 4) : `WF-01 – JobRadar Hourly Job Collector`.
