from __future__ import annotations

import enum
import os
import random

from snake import led_map_v2 as led_map
from snake.types import Color, Direction

# Environment / Mode
SNAKE_DANCE_MODE = os.environ.get("SNAKE_DANCE_MODE", "RASPBERRYPI")

# Direction constants
UP = Direction(0, -1)
DOWN = Direction(0, 1)
LEFT = Direction(-1, 0)
RIGHT = Direction(1, 0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

# Board / Display configuration
WIDTH = len(led_map.MAP[0])
HEIGHT = len(led_map.MAP)
SCALE = 50
NUM_PIXELS = getattr(led_map, "NUM_PIXELS", 102)

# Timing / Speed configuration
PLAYER_GAME_SPEED = 0.15  # Seconds per frame (lower is faster)
AGENT_GAME_SPEED = 0.07  # Seconds per frame (lower is faster)
REFRESH_RATE = 30  # Frames per second
END_SEQUENCE_LENGTH = 5

# Color constants
DARK = Color(2, 4, 0)
BLOCKED = Color(0, 255, 0)

# Portal color constants
PORTALS: dict[tuple[int, int], Color] = {}
for portal in led_map.PORTALS.keys():
    color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    if PORTALS.get(portal) is None:
        PORTALS[portal] = color
        PORTALS[led_map.PORTALS[portal]] = color


class GameMode(enum.Enum):
    AGENT = "agent"
    ML_AGENT = "ml_agent"
    PLAYER = "player"
