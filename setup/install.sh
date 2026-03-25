#!/usr/bin/env bash
# install.sh — oscar-emr-lab one-command setup
# Usage: ./setup/install.sh
# Requires: Docker with Compose plugin (v2)

set -e
cd "$(dirname "$0")/.."

OSCAR_URL="http://localhost:9090/oscar/"
DB_CONTAINER="oscar-lab-db"
OSCAR_CONTAINER="oscar-lab-oscar"

# ── Colours ───────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
info() { echo -e "${YELLOW}→${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      oscar-emr-lab  ·  setup script      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Prerequisites ─────────────────────────────────────────────────────────
info "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || fail "Docker not found. Install Docker Desktop: https://docs.docker.com/get-docker/"
docker info >/dev/null 2>&1      || fail "Docker daemon is not running. Please start Docker and retry."
docker compose version >/dev/null 2>&1 || fail "Docker Compose plugin not found. Update Docker Desktop to v2.x or later."
ok "Docker is ready."

# ── .env ──────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    info "Creating .env from .env.example..."
    cp .env.example .env
    ok ".env created (lab credentials: oscarlab / oscarlab)."
else
    ok ".env already exists."
fi

# ── Pull images ───────────────────────────────────────────────────────────
info "Pulling Docker images (no compilation required)..."
docker compose pull
ok "Images ready."

# ── Start containers ──────────────────────────────────────────────────────
info "Starting containers..."
docker compose up -d
ok "Containers started."

# ── Wait for MariaDB ──────────────────────────────────────────────────────
info "Waiting for MariaDB to be ready..."
for i in $(seq 1 30); do
    if docker exec "$DB_CONTAINER" mysqladmin ping -uroot -poscarlab --silent 2>/dev/null; then
        ok "MariaDB is ready."
        break
    fi
    [ $i -eq 30 ] && fail "MariaDB did not become ready in time. Check: docker logs $DB_CONTAINER"
    sleep 3
done

# ── Wait for OSCAR (Tomcat) ───────────────────────────────────────────────
info "Waiting for OSCAR to start (this takes ~60–90 seconds on first run)..."
for i in $(seq 1 40); do
    HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$OSCAR_URL" 2>/dev/null || true)
    if [ "$HTTP" = "200" ] || [ "$HTTP" = "302" ]; then
        ok "OSCAR is responding (HTTP $HTTP)."
        break
    fi
    [ $i -eq 40 ] && fail "OSCAR did not start in time. Check: docker logs $OSCAR_CONTAINER"
    printf "."
    sleep 5
done
echo ""

# ── Seed database ─────────────────────────────────────────────────────────
info "Seeding database (program, provider enrollment)..."
docker exec -i "$DB_CONTAINER" mysql -uroot -poscarlab oscar < setup/seed.sql
ok "Database seeded."

# ── Patch forward.jsp ─────────────────────────────────────────────────────
info "Applying eChart session patch..."
bash setup/patch_forward_jsp.sh "$OSCAR_CONTAINER"

# ── Done ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓  OSCAR EMR 19 Lab is ready!                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Login URL:  $OSCAR_URL"
echo "  Username:   oscardoc"
echo "  Password:   mac2002"
echo "  PIN:        1117"
echo ""
echo "  eChart URL: http://localhost:9090/oscar/oscarEncounter/IncomingEncounter.do"
echo "              ?case_program_id=10034&demographicNo=DEMO_NO&status=B"
echo ""
echo "  Add patients:"
echo "    1. Download Synthea:  patients/README.md"
echo "    2. Run import:        python3 patients/synthea_oscar_import.py /path/to/fhir/"
echo ""
echo "  Stop:   docker compose down"
echo "  Reset:  docker compose down -v  (wipes all data)"
echo ""
