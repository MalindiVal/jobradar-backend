#!/bin/sh
# Crée l'utilisateur et la base dédiés à n8n. Exécuté par l'image postgres
# uniquement à l'initialisation d'un volume vide.
set -eu

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v n8n_user="$N8N_DB_USER" -v n8n_password="$N8N_DB_PASSWORD" -v n8n_db="$N8N_DB_NAME" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'n8n_user', :'n8n_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'n8n_user')\gexec
SELECT format('CREATE DATABASE %I OWNER %I', :'n8n_db', :'n8n_user')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'n8n_db')\gexec
SQL
