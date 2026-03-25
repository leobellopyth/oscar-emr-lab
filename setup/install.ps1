# install.ps1 — One-command OSCAR EMR lab setup (Windows PowerShell)
# Usage: .\setup\install.ps1
#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoDir = Split-Path $PSScriptRoot -Parent
$EnvFile = Join-Path $RepoDir ".env"
$EnvExample = Join-Path $RepoDir ".env.example"

Write-Host "=== OSCAR EMR Lab Setup ===" -ForegroundColor Cyan

# ── 1. Prerequisites check ────────────────────────────────────────────────
foreach ($cmd in @("docker", "python")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Error "$cmd not found. Install it and re-run."
    }
}

# ── 2. Create .env from example if not present ────────────────────────────
if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "Created .env — edit MYSQL_ROOT_PASSWORD, then re-run." -ForegroundColor Yellow
    exit 0
}

$EnvContent = Get-Content $EnvFile -Raw
if ($EnvContent -match "change_me_before_use") {
    Write-Error "Set a real MYSQL_ROOT_PASSWORD in .env before continuing."
}

# ── 3. Start containers ───────────────────────────────────────────────────
Write-Host "[1/4] Starting Docker containers..."
Push-Location $RepoDir
docker compose up -d

# ── 4. Wait for MariaDB ───────────────────────────────────────────────────
Write-Host "[2/4] Waiting for MariaDB..."
$RootPass = ($EnvContent | Select-String "MYSQL_ROOT_PASSWORD=(.+)").Matches[0].Groups[1].Value.Trim()
$DbContainer = docker compose ps -q db
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    $result = docker exec $DbContainer mysqladmin ping -uroot "-p$RootPass" --silent 2>$null
    if ($LASTEXITCODE -eq 0) { $ready = $true; Write-Host "  MariaDB ready."; break }
    Start-Sleep 2
}
if (-not $ready) { Write-Error "MariaDB did not become ready in time." }

# ── 5. Seed ───────────────────────────────────────────────────────────────
Write-Host "[3/4] Seeding provider and program..."
$SeedSql = Join-Path $PSScriptRoot "seed.sql"
Get-Content $SeedSql | docker exec -i $DbContainer mysql -uroot "-p$RootPass" oscar
Write-Host "  Seed complete."

# ── 6. Done ───────────────────────────────────────────────────────────────
$OscarPort = if ($EnvContent -match "OSCAR_PORT=(\d+)") { $Matches[1] } else { "9090" }
Write-Host "[4/4] Done." -ForegroundColor Green
Write-Host ""
Write-Host "  OSCAR is starting at: http://localhost:$OscarPort/oscar/" -ForegroundColor Cyan
Write-Host "  Login:  oscardoc / mac2002"
Write-Host ""
Write-Host "  To import synthetic patients:"
Write-Host "    pip install pymysql"
Write-Host "    python patients\synthea_oscar_import.py C:\path\to\fhir\"
Write-Host ""
Write-Host "  OSCAR takes ~60 seconds to finish loading after containers start."
Pop-Location
