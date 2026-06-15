#!/bin/bash

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:/home/site/wwwroot"

# Install dependencies (if needed)
pip install -r requirements.txt

# Wait for Postgres to be available (tries for ~60s)
echo "Waiting for database to become available..."
TRIES=0
MAX_TRIES=30
until python - <<'PY' 2>/dev/null
import os,sys
from sqlalchemy import create_engine
url = os.environ.get('SQLALCHEMY_DATABASE_URL') or os.environ.get('DATABASE_URL')
if not url:
	print('no_db_url')
	sys.exit(2)
try:
	create_engine(url).connect()
	print('ok')
	sys.exit(0)
except Exception as e:
	print('notready', e)
	sys.exit(1)
PY
do
	TRIES=$((TRIES+1))
	if [ $TRIES -ge $MAX_TRIES ]; then
		echo "Database did not become available after $((MAX_TRIES*2)) seconds. Proceeding anyway."
		break
	fi
	sleep 2
done

# Ensure Alembic migrations folder exists
mkdir -p alembic/versions

count_revisions() {
	find alembic/versions -maxdepth 1 -name '*.py' 2>/dev/null | wc -l | tr -d ' '
}

remove_noop_revision() {
	local latest_file="$1"
	if [ -n "$latest_file" ] && ! grep -q "op\." "$latest_file"; then
		echo "No DB-op changes detected in $latest_file — removing no-op revision"
		rm -f "$latest_file"
		return 1
	fi
	if [ -n "$latest_file" ]; then
		echo "Autogenerate created $latest_file with changes"
	fi
	return 0
}

REVISION_COUNT=$(count_revisions)

if [ "${REVISION_COUNT}" = "0" ]; then
	if [ "${AUTO_MIGRATE}" = "true" ]; then
		echo "No Alembic revisions found — AUTO_MIGRATE=true, bootstrapping initial migration from models"
		python -m alembic revision --autogenerate -m "initial $(date -u +%Y%m%d%H%M%S)" || {
			echo "ERROR: Failed to create initial autogenerate revision"
			exit 1
		}
		LATEST_FILE=$(ls -t alembic/versions/*.py 2>/dev/null | head -n1)
		if ! remove_noop_revision "$LATEST_FILE"; then
			echo "ERROR: Initial autogenerate produced no schema changes — check model imports in alembic/env.py"
			exit 1
		fi
		REVISION_COUNT=$(count_revisions)
		if [ "${REVISION_COUNT}" = "0" ]; then
			echo "ERROR: Bootstrap did not leave any revision files in alembic/versions/*.py"
			exit 1
		fi
	else
		echo "ERROR: No Alembic revision files found in alembic/versions/*.py"
		echo "Refusing to run migrations — set AUTO_MIGRATE=true to bootstrap from models, or provide revision files."
		exit 1
	fi
elif [ "${AUTO_MIGRATE}" = "true" ]; then
	echo "AUTO_MIGRATE=true — checking for model changes and creating autogenerate revision if needed"
	python -m alembic revision --autogenerate -m "autogen $(date -u +%Y%m%d%H%M%S)" || true
	LATEST_FILE=$(ls -t alembic/versions/*.py 2>/dev/null | head -n1)
	remove_noop_revision "$LATEST_FILE" || true
else
	echo "AUTO_MIGRATE not set to 'true' — skipping autogenerate step"
fi

# Apply migrations to the database
echo "Applying Alembic migrations (upgrade head)"
python -m alembic upgrade head

# Run the application: use multiple workers for production
APP_PORT="${APP_PORT:-3090}"
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b "0.0.0.0:${APP_PORT}" main:app

