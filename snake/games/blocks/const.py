from __future__ import annotations

from snake.const import WIDTH
from snake.types import Color, Effect

# Playfield boundaries on the cylindrical LED screen.
# The screen wraps horizontally across all columns (x in 0..WIDTH-1).
PLAYFIELD_MIN_X = 0
PLAYFIELD_MAX_X = WIDTH - 1
PLAYFIELD_MIN_Y = 0
PLAYFIELD_MAX_Y = 8
PLAYFIELD_BOTTOM_Y = 8

# Speed and timing configurations
BLOCKS_PLAYER_SPEED = 0.20  # Seconds per tick for player
BLOCKS_AGENT_SPEED = 0.12  # Seconds per tick for agent
DEFAULT_FALL_INTERVAL_TICKS = 4  # Gravity drop every 4 ticks (~0.48s)
LINE_CLEAR_FLASH_TICKS = 6  # Ticks to flash full rows before collapse

# Colors (GRB ordering for hardware compatibility)
# Cyan, Yellow, Purple, Green, Red, Blue, Orange
TETROMINO_COLORS: dict[str, Color] = {
    "I": Color(255, 0, 255),  # Cyan
    "O": Color(255, 255, 0),  # Yellow
    "T": Color(0, 255, 255),  # Purple / Magenta
    "S": Color(255, 0, 0),  # Green
    "Z": Color(0, 255, 0),  # Red
    "J": Color(0, 0, 255),  # Blue
    "L": Color(128, 255, 0),  # Orange
}

LINE_CLEAR_COLOR = Color(255, 255, 255, Effect.FLASH)

# Precomputed rotation states for all 7 standard tetrominoes
TETROMINOES: dict[str, list[list[tuple[int, int]]]] = {
    "I": [
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "O": [
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (0, 1), (1, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}
