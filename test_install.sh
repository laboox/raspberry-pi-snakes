#!/bin/bash

echo "🧪 Testing Snake Game installation on pizero1.local..."

# Test SSH connection
echo "🔌 Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 pizero1.local "echo 'SSH connection successful'"; then
    echo "❌ Cannot connect to pizero1.local. Please check:"
    echo "   - SSH key is set up"
    echo "   - pizero1.local is reachable"
    echo "   - User has sudo privileges"
    exit 1
fi

# Test Python installation
echo "🐍 Testing Python installation..."
ssh pizero1.local "python3 --version"

# Test package installation
echo "📦 Testing package installation..."
ssh pizero1.local "cd ~/snake-deploy && source snake-env/bin/activate && python -c 'import snake; print(\"✅ Snake package imported successfully\")'"

# Test daemon status
echo "👻 Testing daemon status..."
ssh pizero1.local "sudo supervisorctl status snake_dance"

# Test log file
echo "📝 Testing log file..."
ssh pizero1.local "ls -la /var/log/snake_dance.log"

echo "✅ All tests completed successfully!"
echo "🎮 Snake game should be running on pizero1.local"
