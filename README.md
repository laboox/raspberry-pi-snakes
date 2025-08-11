# Snake Game

A Snake game implementation with LED matrix display and joystick support, designed for Raspberry Pi with NeoPixel LED strips.

## Features

- Classic Snake gameplay with AI agent
- LED matrix visualization using NeoPixel strips
- Joystick/gamepad support via pygame
- BFS pathfinding algorithm for intelligent snake movement
- Portal system for enhanced gameplay
- Configurable game speed and LED colors

## Requirements

- Python 3.8 or higher
- Raspberry Pi (recommended for LED matrix support)
- NeoPixel LED strip (100 LEDs)
- Joystick/gamepad (optional)
- SPI interface enabled on Raspberry Pi

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/snake-game.git
cd snake-game
```

2. Install the package in development mode:
```bash
pip install -e .
```

3. Install development dependencies (optional):
```bash
pip install -e ".[dev]"
```

### Using pip

```bash
pip install snake-game
```

## Usage

### Running the Game

```bash
# Run the game directly
python -m snake.main

# Or use the installed script
snake
```

### Configuration

The game can be configured by modifying the constants in `snake/main.py`:

- `GAME_SPEED`: Controls game speed (lower = faster)
- `INITIAL_SNAKE_LENGTH`: Starting length of the snake
- `SNAKE_HEAD`, `SNAKE_BODY`, `FOOD`: LED colors for game elements
- `NUM_PIXELS`: Number of LEDs in your strip

## Development

### Setting up the development environment

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Install pre-commit hooks (optional):
```bash
pre-commit install
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

Run all quality checks:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Type checking
mypy .

# Run tests
pytest

# Run all checks
black . && isort . && flake8 && mypy . && pytest
```

### Building and Publishing

Build the package:
```bash
python -m build
```

This will create distribution files in the `dist/` directory.

## Project Structure

```
snake/
├── main.py          # Main game logic
├── led_map.py       # LED matrix mapping and portals
└── led_map_test.py  # Tests for LED mapping
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the quality checks
5. Submit a pull request

## Troubleshooting

### LED Matrix Issues

- Ensure SPI is enabled on your Raspberry Pi
- Check that the NeoPixel library is properly installed
- Verify the LED count matches your hardware

### Joystick Issues

- Make sure pygame is installed
- Check that your joystick is recognized by the system
- Try different joystick configurations in the code

## Acknowledgments

- Adafruit for the NeoPixel library
- Pygame community for joystick support
- The classic Snake game for inspiration
