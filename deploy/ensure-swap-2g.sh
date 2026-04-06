#!/usr/bin/env bash
# Run on the VPS (once) before heavy `docker compose build` if RAM is tight (e.g. 1–2 GB).
# Adds a 2 GiB swap file so the OOM killer is less likely to stop npm/Next during image build.
# Requires sudo. Idempotent: skips if our swap file is already active.

set -euo pipefail

SWAP_PATH="${SWAP_PATH:-/swapfile_och_2g}"
SIZE_MB="${SIZE_MB:-2048}"

if swapon --show 2>/dev/null | grep -qF "$SWAP_PATH"; then
  echo "Swap already active at $SWAP_PATH"
  swapon --show
  exit 0
fi

if [[ -f "$SWAP_PATH" ]] && ! swapon --show 2>/dev/null | grep -qF "$SWAP_PATH"; then
  echo "Activating existing $SWAP_PATH"
  sudo swapon "$SWAP_PATH" || true
fi

if swapon --show 2>/dev/null | grep -q .; then
  echo "Another swap is already enabled (not creating $SWAP_PATH):"
  swapon --show
  exit 0
fi

echo "Creating ${SIZE_MB}M swap at $SWAP_PATH (needs sudo)..."
sudo fallocate -l "${SIZE_MB}M" "$SWAP_PATH" 2>/dev/null || \
  sudo dd if=/dev/zero of="$SWAP_PATH" bs=1M count="$SIZE_MB" status=progress
sudo chmod 600 "$SWAP_PATH"
sudo mkswap "$SWAP_PATH"
sudo swapon "$SWAP_PATH"

if ! grep -qF "$SWAP_PATH" /etc/fstab 2>/dev/null; then
  echo "$SWAP_PATH none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
  echo "Added $SWAP_PATH to /etc/fstab for reboot persistence."
fi

echo "Done."
free -h || true
swapon --show
