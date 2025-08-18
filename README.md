# Snake Game for Raspberry Pi

A snake game designed to run on Raspberry Pi with LED matrix display using CircuitPython and Pygame.

## Features

- Classic snake gameplay
- LED matrix display support
- Joystick input support
- AI agent mode with BFS pathfinding
- Player mode with manual control
- Automatic restart and daemon support

## Hardware Requirements

- Raspberry Pi (tested on Pi Zero)
- LED matrix display
- Joystick/controller (optional)
- SPI interface for LED control

## Dependencies

- Python 3.7+
- pygame
- adafruit-circuitpython-neopixel-spi
- adafruit-blinka

## Installation

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game
python -m snake.main
```

### Deployment to Remote Host

1. **Build and deploy to pizero1.local:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Manual deployment:**
   ```bash
   # Build package
   python3 setup.py sdist bdist_wheel

   # Copy to remote host
   scp dist/*.whl pizero1.local:~/
   scp requirements.txt pizero1.local:~/

   # Install on remote host
   ssh pizero1.local
   pip3 install *.whl
   ```

## Daemon Management

The game can run as a daemon using supervisord:

```bash
# Check status
sudo supervisorctl status snake_dance

# Start daemon
sudo supervisorctl start snake_dance

# Stop daemon
sudo supervisorctl stop snake_dance

# Restart daemon
sudo supervisorctl restart snake_dance

# View logs
tail -f /var/log/snake_dance.log
```

## Game Controls

- **Joystick**: Control snake direction
- **Button press**: Switch between AI and Player modes
- **Game automatically restarts** when game over

## Configuration

The LED matrix mapping is defined in `snake/led_map_v2.py`. Adjust the MAP array to match your specific LED matrix layout.

## Troubleshooting

1. **Permission issues**: Ensure SPI is enabled and user has proper permissions
2. **Display not working**: Check LED matrix connections and SPI configuration
3. **Game not starting**: Check logs at `/var/log/snake_dance.log`

## Development

To modify the game:

1. Edit `snake/main.py` for game logic
2. Edit `snake/led_map_v2.py` for LED mapping
3. Rebuild and redeploy using `./deploy.sh`
