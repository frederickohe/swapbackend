#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/var/www/swapbackend"

cd "$REPO_DIR"
git fetch origin main
git reset --hard origin/main

# Compose can leave a stopped container holding container_name=swappro_backend,
# then fail recreate with: "Conflict. The container name is already in use".
# Force-remove any backend containers so `up` can allocate the name cleanly.
docker ps -aq --filter name='swappro_backend' | xargs -r docker rm -f >/dev/null || true

docker compose up --build -d --remove-orphans

echo "swapbackend deploy complete"
