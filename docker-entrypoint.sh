#!/usr/bin/env bash
set -e

echo "🎸 ======================================================"
echo "   Empório AI — Intelligent Customer Service Agent"
echo "   Container Entrypoint Initializer"
echo "=========================================================="

# Check if SQLite database exists
DB_FILE="emporio.db"
if [[ "$DATABASE_URL" == *"data/emporio.db"* ]]; then
    DB_FILE="data/emporio.db"
fi

if [ ! -f "$DB_FILE" ] || [ ! -s "$DB_FILE" ]; then
    echo "⚡ [Init] Database '$DB_FILE' not found or empty."
    echo "⚡ [Init] Executing automated ingestion pipeline (CSVs + Policies PDF)..."
    python scripts/ingest.py
    echo "✅ [Init] Ingestion completed. Ready to serve requests."
else
    echo "ℹ️ [Init] Existing SQLite database detected at '$DB_FILE'."
fi

echo "🚀 [Init] Launching application with command: $@"
exec "$@"
