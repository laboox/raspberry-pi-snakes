# Snake Game for Raspberry Pi

A snake game designed to run on Raspberry Pi with an addressable LED matrix display using CircuitPython and Pygame.

## Features

- Classic snake gameplay
- Addressable LED display support
- Joystick input support
- AI agent mode with BFS pathfinding
- Player mode with manual control
- Automatic restart and daemon support

## Hardware Requirements

- Raspberry Pi (tested on Pi Zero 2W and Pi 5)
- Addressable LEDs compatible with NeoPixel
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
# Create a virtual environment
python -m venv venv --system-site-packages

# Install build
pip install build
```

### Deployment to Remote Host

1. **Build and deploy to host:**
   ```bash
   HOST=raspberrypi.local
   chmod +x deploy.sh
   ./deploy.sh $HOST
   ```

## Game Controls

- **Start button**: Switch to Player mode
- **Back button**: Switch to AI mode
- **Joystick**: Control snake direction
- **Game automatically restarts** when game over

## Configuration

The LED matrix mapping is defined in `snake/led_map_v2.py`. Adjust the MAP array to match your specific LED matrix layout.

## Troubleshooting

1. **Installation**: Install Blinka library properly using [this guide](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) and not pip
2. **Disable audio on SPI**: If you are using SPI, disable Audio
3. **Permission issues**: Ensure SPI is enabled and user has proper permissions
4. **Display not working**: Check LED matrix connections and SPI configuration
5. **Game not starting**: Check journalctl using `journalctl --user-unit snake_dance`

## Development

To modify the game:

1. Edit `snake/main.py` for game logic
2. Edit `snake/led_map_v2.py` for LED mapping
3. Rebuild and redeploy using `./install.sh $HOSTNAME`
4. Install Pre-commit before making a PR `pip install pre-commit && pre-commit install`
