#!/usr/local/bin/zsh

# This script is used to install the Snake Game on a remote machine.
# assuming that the game is already deployed on the remote machine.

# Snake Game Deployment Script
set -e

# Check if hostname argument is provided
if [ $# -eq 0 ]; then
    echo "❌ Error: Hostname argument is required"
    echo "Usage: $0 <hostname>"
    echo "Example: $0 raspberrypi.local"
    exit 1
fi

HOSTNAME="$1"

echo "🐍 Building and deploying Snake Game to $HOSTNAME..."

# Build the package
echo "📦 Building Python package..."
rm -rf dist
uv build --wheel

echo "📤 Copying package to $HOSTNAME..."
scp dist/*.whl "$HOSTNAME":~/snake-deploy/

echo "🔧 Reinstalling snake-game..."
ssh "$HOSTNAME" "~/snake-deploy/venv/bin/pip uninstall --yes snake-game"
ssh "$HOSTNAME" "~/snake-deploy/venv/bin/pip install ~/snake-deploy/*.whl"

echo "🔄 Restarting snake_dance service..."
ssh "$HOSTNAME" "systemctl --user restart snake_dance"
