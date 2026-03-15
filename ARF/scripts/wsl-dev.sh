#!/usr/bin/env bash
# FLOSSIOULLK Rose Forest – WSL2 dev shell entry
# Usage (from Windows): wsl -d Ubuntu -- bash /mnt/c/~shit/FLOSS/ARF/scripts/wsl-dev.sh
# Usage (from WSL):     bash ~/dev/ARF/scripts/wsl-dev.sh

set -euo pipefail

# Locate project
if [ -d "$HOME/dev/ARF" ]; then
    PROJECT="$HOME/dev/ARF"
elif [ -d "/mnt/c/~shit/FLOSS/ARF" ]; then
    PROJECT="/mnt/c/~shit/FLOSS/ARF"
else
    echo "ERROR: Project not found. Run sync-to-wsl.sh first."
    exit 1
fi

# Source nix
if [ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
    . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi

cd "$PROJECT"
echo "Entering nix dev shell at $PROJECT..."
exec nix develop --accept-flake-config
