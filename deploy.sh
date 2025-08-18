#!/bin/bash

# Snake Game Deployment Script for pizero1.local
set -e

echo "🐍 Building and deploying Snake Game to pizero1.local..."

# Build the package
echo "📦 Building Python package..."
python3 setup.py sdist bdist_wheel

# Create deployment directory
echo "📁 Creating deployment directory..."
ssh pizero1.local "mkdir -p ~/snake-deploy"

# Copy files to remote host
echo "📤 Copying files to pizero1.local..."
scp dist/*.whl pizero1.local:~/snake-deploy/
scp requirements.txt pizero1.local:~/snake-deploy/
scp service/snake_dance.ini pizero1.local:~/snake-deploy/

# Install on remote host
echo "🔧 Installing on pizero1.local..."
ssh pizero1.local << 'EOF'
    cd ~/snake-deploy

    # Update system packages
    sudo apt-get update

    # Install Python dependencies
    sudo apt-get install -y python3-pip python3-venv supervisor

    # Create virtual environment
    python3 -m venv snake-env
    source snake-env/bin/activate

    # Install the snake game package
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install *.whl

    # Setup daemon
    sudo cp snake_dance.ini /etc/supervisor/conf.d/
    sudo mkdir -p /var/log/snake
    sudo chown $USER:$USER /var/log/snake

    # Reload supervisor
    sudo supervisorctl reread
    sudo supervisorctl update

    echo "✅ Installation complete!"
    echo "🚀 Starting snake game daemon..."
    sudo supervisorctl start snake_dance

    echo "📊 Status:"
    sudo supervisorctl status snake_dance
EOF

echo "🎉 Deployment complete! Snake game is now running on pizero1.local"
echo "📝 To check status: ssh pizero1.local 'sudo supervisorctl status snake_dance'"
echo "📝 To view logs: ssh pizero1.local 'tail -f /var/log/snake_dance.log'"
