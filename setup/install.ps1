# install.ps1 — oscar-emr-lab setup for Windows (PowerShell)
# Usage: .\setup\install.ps1
# Requires: Docker Desktop for Windows

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot)

$OSCAR_URL    = "http://localhost:9090/oscar/"
$DB_CONTAINER = "oscar-lab-db"
$OSC_CONTAINER= "oscar-lab-oscar"

function ok   { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function info { param($msg) Write-Host "→ $msg" -ForegroundColor Yellow }
function fail { param($msg) Write-Host "✗ $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗"
Write-Host "║      oscar-emr-lab  ·  setup script      ║"
Write-Host "╚══════════════════════════════════════════╝"
Write-Host ""

# Prerequisites
info "Checking prerequisites..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { fail "Docker not found. Install Docker Desktop: https://docs.docker.com/get-docker/" }
docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { fail "Docker daemon not running. Start Docker Desktop and retry." }
ok "Docker is ready."

# .env
if (-not (Test-Path ".env")) {
    info "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env"
    ok ".env created (lab credentials: oscarlab / oscarlab)."
} else {
    ok ".env already exists."
}

# Pull images
info "Pulling Docker images (no compilation required)..."
docker compose pull
ok "Images ready."

# Start
info "Starting containers..."
docker compose up -d
ok "Containers started."

# Wait for MariaDB
info "Waiting for MariaDB..."
for ($i = 1; $i -le 30; $i++) {
    $ping = docker exec $DB_CONTAINER mysqladmin ping -uroot -poscarlab --silent 2>&1
    if ($LASTEXITCODE -eq 0) { ok "MariaDB is ready."; break }
    if ($i -eq 30) { fail "MariaDB did not start. Check: docker logs $DB_CONTAINER" }
    Start-Sleep 3
}

# Wait for OSCAR
info "Waiting for OSCAR to start (~60-90 seconds on first run)..."
for ($i = 1; $i -le 40; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri $OSCAR_URL -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($resp.StatusCode -in @(200, 302)) { ok "OSCAR is responding."; break }
    } catch {}
    if ($i -eq 40) { fail "OSCAR did not start. Check: docker logs $OSC_CONTAINER" }
    Write-Host "." -NoNewline
    Start-Sleep 5
}
Write-Host ""

# Seed
info "Seeding database..."
Get-Content "setup\seed.sql" | docker exec -i $DB_CONTAINER mysql -uroot -poscarlab oscar
ok "Database seeded."

# Patch
info "Applying eChart session patch..."
$JSP = "/usr/local/tomcat/webapps/oscar/casemgmt/forward.jsp"
$WORK = "/usr/local/tomcat/work/Catalina/localhost/oscar/org/apache/jsp/casemgmt"
$already = docker exec $OSC_CONTAINER grep -c "case_program_id fallback" $JSP 2>&1
if ($already -gt 0) {
    ok "forward.jsp already patched."
} else {
    docker exec $OSC_CONTAINER sed -i `
      's|    String useNewCaseMgmt;|    // case_program_id fallback (oscar-emr-lab patch)\n    String _cpid = request.getParameter(\"case_program_id\");\n    if (_cpid != null \&\& _cpid.length() > 0) { session.setAttribute(\"case_program_id\", _cpid); }\n    else if (session.getAttribute(\"case_program_id\") == null) { session.setAttribute(\"case_program_id\", \"10034\"); }\n    String useNewCaseMgmt;|' `
      $JSP
    docker exec $OSC_CONTAINER rm -f "$WORK/forward_jsp.class" "$WORK/forward_jsp.java" 2>&1 | Out-Null
    ok "forward.jsp patched."
}

# Done
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✓  OSCAR EMR 19 Lab is ready!                               ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Login URL:  $OSCAR_URL"
Write-Host "  Username:   oscardoc"
Write-Host "  Password:   mac2002"
Write-Host "  PIN:        1117"
Write-Host ""
Write-Host "  eChart:     http://localhost:9090/oscar/oscarEncounter/IncomingEncounter.do"
Write-Host "              ?case_program_id=10034&demographicNo=DEMO_NO&status=B"
Write-Host ""
Write-Host "  Add patients: See patients\README.md"
Write-Host ""
Write-Host "  Stop:   docker compose down"
Write-Host "  Reset:  docker compose down -v  (wipes all data)"
Write-Host ""
