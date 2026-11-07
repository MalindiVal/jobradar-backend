# Vérifie que l'environnement local JobRadar (docker compose) est opérationnel.
# Usage : powershell -ExecutionPolicy Bypass -File scripts/check-local.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$failed = 0

function Report($ok, $label, $detail = "") {
    if ($ok) { Write-Host "[OK]   $label $detail" -ForegroundColor Green }
    else { Write-Host "[KO]   $label $detail" -ForegroundColor Red; $script:failed++ }
}

# 1. Fichier .env et secrets obligatoires
$envFile = Join-Path $root ".env"
$vars = @{}
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*([A-Z0-9_]+)\s*=\s*(.*)$') { $vars[$Matches[1]] = $Matches[2].Trim() }
    }
}
Report (Test-Path $envFile) ".env présent"
foreach ($name in "SECRET_KEY", "JOBRADAR_INTERNAL_KEY", "N8N_ENCRYPTION_KEY") {
    $value = $vars[$name]
    Report ($value -and $value -notmatch "change-me") "$name renseignée"
}

# 2. Conteneurs
try {
    $ps = docker compose --project-directory $root ps --format "{{.Service}} {{.State}}" 2>$null
    foreach ($svc in "db", "api", "n8n") {
        $state = ($ps | Where-Object { $_ -like "$svc *" }) -replace "^$svc ", ""
        Report ($state -eq "running") "Conteneur $svc" "($state)"
    }
} catch { Report $false "docker compose" "(Docker non disponible : $_)" }

# 3. Services HTTP
function Probe($label, $url, $headers = @{}) {
    try {
        $r = Invoke-WebRequest -Uri $url -Headers $headers -UseBasicParsing -TimeoutSec 5
        Report ($r.StatusCode -eq 200) $label "($url)"
    } catch { Report $false $label "($url : $($_.Exception.Message))" }
}
Probe "API /health" "http://localhost:8000/health"
Probe "API /internal/ping (clé interne)" "http://localhost:8000/internal/ping" @{ "X-API-Key" = $vars["JOBRADAR_INTERNAL_KEY"] }
Probe "n8n /healthz" "http://localhost:5678/healthz"

# 4. Base n8n et migrations
try {
    $dbs = docker compose --project-directory $root exec -T db psql -U jobradar -d jobradar -tAc "SELECT datname FROM pg_database WHERE datname = 'n8n'"
    Report ($dbs -match "n8n") "Base PostgreSQL n8n"
    $rev = docker compose --project-directory $root exec -T db psql -U jobradar -d jobradar -tAc "SELECT version_num FROM alembic_version"
    Report ($rev -match "0003_mvp_data_model") "Migration Alembic" "($rev)"
} catch { Report $false "PostgreSQL" "($_)" }

if ($failed) { Write-Host "`n$failed vérification(s) en échec." -ForegroundColor Red; exit 1 }
Write-Host "`nEnvironnement local opérationnel." -ForegroundColor Green
