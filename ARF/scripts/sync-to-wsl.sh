#!/usr/bin/env bash
# Sync project from Windows mount to native WSL filesystem for build performance.
# Usage (from WSL): bash /mnt/c/~shit/FLOSS/ARF/scripts/sync-to-wsl.sh

set -euo pipefail

SRC="/mnt/c/~shit/FLOSS/ARF"
DEST="$HOME/dev/ARF"

mkdir -p "$DEST"

rsync -av --delete \
    --exclude target \
    --exclude node_modules \
    --exclude .git \
    --exclude '*.zip' \
    "$SRC/" "$DEST/"

echo "Synced to $DEST"
echo "Run: cd $DEST && bash scripts/wsl-dev.sh"
