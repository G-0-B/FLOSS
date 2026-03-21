#!/usr/bin/env bash
set -euo pipefail

LOG="/tmp/nix-setup.log"
echo "=== FLOSSIOULLK WSL2 Nix Setup ===" | tee "$LOG"
echo "Started: $(date)" | tee -a "$LOG"

# Step 1: Check if nix is already installed
if command -v nix &>/dev/null; then
    echo "Nix already installed: $(nix --version)" | tee -a "$LOG"
else
    echo "Installing Nix via Determinate Systems installer..." | tee -a "$LOG"
    curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix \
        | sh -s -- install --no-confirm 2>&1 | tee -a "$LOG"
    echo "Nix install completed" | tee -a "$LOG"
fi

# Source nix profile
if [ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
    . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
elif [ -f "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
    . "$HOME/.nix-profile/etc/profile.d/nix.sh"
fi

# Step 2: Verify nix works
echo "" | tee -a "$LOG"
echo "=== Nix verification ===" | tee -a "$LOG"
nix --version 2>&1 | tee -a "$LOG"
nix config show | grep experimental-features 2>&1 | tee -a "$LOG" || true

# Step 3: Check project access
echo "" | tee -a "$LOG"
echo "=== Project access ===" | tee -a "$LOG"
PROJ="/mnt/c/~shit/FLOSS/ARF"
if [ -f "$PROJ/flake.nix" ]; then
    echo "flake.nix found at $PROJ" | tee -a "$LOG"
else
    echo "ERROR: flake.nix not found at $PROJ" | tee -a "$LOG"
    exit 1
fi

echo "" | tee -a "$LOG"
echo "=== Setup complete ===" | tee -a "$LOG"
echo "Next: cd $PROJ && nix develop" | tee -a "$LOG"
echo "Finished: $(date)" | tee -a "$LOG"
