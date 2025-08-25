#!/usr/local/bin/zsh

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
python -m build --wheel

# Create deployment directory
echo "📁 Creating deployment directory..."
ssh "$HOSTNAME" "mkdir -p ~/snake-deploy"
ssh "$HOSTNAME" "mkdir -p ~/.config/systemd/user"

# Copy files to remote host
echo "📤 Copying files to $HOSTNAME..."
scp dist/*.whl "$HOSTNAME":~/snake-deploy/
scp service/snake_dance.service "$HOSTNAME":~/snake-deploy/

# Install on remote host
echo "🔧 Installing on $HOSTNAME..."
ssh "$HOSTNAME" << 'EOF'
    cd ~/snake-deploy

    # Update system packages
    sudo apt-get update

    # Upgrade system packages
    sudo apt-get upgrade -y

    # Install Python dependencies
    sudo apt-get install -y python3-pip python3-venv python3-systemd

    # Create virtual environment
    python3 -m venv --system-site-packages venv
    source venv/bin/activate

    # Update pip itself
    pip install --upgrade pip

    # Install Blinka dependencies
    pip3 install --upgrade adafruit-python-shell
    wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
    yes no | sudo -E env PATH=$PATH python3 raspi-blinka.py

    # Install the snake game package
    pip install *.whl

    # Setup daemon
    sed -i "s#/home/sina/projects/snake/venv/bin#$HOME/snake-deploy/venv/bin#g" snake_dance.service
    cp snake_dance.service ~/.config/systemd/user/snake_dance.service

    # Start the service
    systemctl --user enable snake_dance
    systemctl --user start snake_dance

    echo "✅ Installation complete!"

    echo "📊 Status:"
    systemctl --user status snake_dance

    # It is required to reboot the system to load the Blinka dependencies
    echo "🔄 Rebooting..."
    sudo reboot
EOF

echo "🎉 Deployment complete! Snake game is now running on $HOSTNAME"
echo "📝 To check status: ssh $HOSTNAME 'systemctl --user status snake_dance'"
