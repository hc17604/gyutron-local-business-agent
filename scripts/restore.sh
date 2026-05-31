#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: scripts/restore.sh data/backups/backup.zip"
  exit 1
fi

cd "$(dirname "$0")/.."
mkdir -p data/.restore_tmp
unzip -o "$1" -d data/.restore_tmp
cp -f data/.restore_tmp/db/gyutron.sqlite3 data/db/gyutron.sqlite3
rm -rf data/.restore_tmp
echo "Restore completed from $1"
