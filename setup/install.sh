#!/usr/bin/env bash
# install.sh — One-command OSCAR EMR lab setup (Linux / macOS)
# Usage: bash setup/install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== OSCAR EMR Lab Setup ==="

# ── 1. Prerequisites check ────────────────────────────────────────────────
for cmd in docker python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found. Install it and re-run."
        exit 1
    fi
done

# ── 2. Create .env from example if not present ────────────────────────────
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo "Created .env — edit it to set a secure MYSQL_ROOT_PASSWORD, then re-run."
    exit 0
fi

# Abort if password is still the placeholder
if grep -q "change_me_before_use" "$REPO_DIR/.env"; then
    echo "ERROR: Set a real MYSQL_ROOT_PASSWORD in .env before continuing."
    exit 1
fi

# ── 3. Start containers ───────────────────────────────────────────────────
echo "[1/4] Starting Docker containers..."
cd "$REPO_DIR"
docker compose up -d

# ── 4. Wait for MariaDB ───────────────────────────────────────────────────
echo "[2/4] Waiting for MariaDB to be ready..."
DB_CONTAINER=$(docker compose ps -q db)
for i in $(seq 1 30); do
    if docker exec "$DB_CONTAINER" mysqladmin ping -uroot \
       -p"$(grep MYSQL_ROOT_PASSWORD .env | cut -d= -f2)" \
       --silent 2>/dev/null; then
        echo "  MariaDB ready."
        break
    fi
    sleep 2
done

# ── 5. Seed provider and program ──────────────────────────────────────────
echo "[3/4] Seeding provider and program..."
ROOT_PASS=$(grep MYSQL_ROOT_PASSWORD .env | cut -d= -f2)
docker exec -i "$DB_CONTAINER" \
    mysql -uroot -p"$ROOT_PASS" oscar \
    < "$SCRIPT_DIR/seed.sql" && echo "  Seed complete." || echo "  Seed skipped (already seeded)."

# ── 6. Done ───────────────────────────────────────────────────────────────
OSCAR_PORT=$(grep OSCAR_PORT .env | cut -d= -f2)
OSCAR_PORT=${OSCAR_PORT:-9090}
echo "[4/4] Done."
echo ""
echo "  OSCAR is starting at: http://localhost:${OSCAR_PORT}/oscar/"
echo "  Login:  oscardoc / mac2002"
echo ""
echo "  To import synthetic patients:"
echo "    pip install pymysql"
echo "    python3 patients/synthea_oscar_import.py /path/to/fhir/"
echo ""
echo "  OSCAR takes ~60 seconds to finish loading after containers start."
