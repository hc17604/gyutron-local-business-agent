#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/backups
STAMP="$(date +%Y%m%d-%H%M%S)"
zip -r "data/backups/gyutron-manual-$STAMP.zip" data/db data/reports data/config -x "data/uploads/*"
echo "Created data/backups/gyutron-manual-$STAMP.zip"
