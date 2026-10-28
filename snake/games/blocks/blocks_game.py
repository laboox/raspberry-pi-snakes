from __future__ import annotations

import random
from typing import Any

from snake import led_map_v2 as led_map
from snake.const import DOWN, HEIGHT, LEFT, RIGHT, UP, WIDTH
from snake.games.base_game import BaseGame
from snake.games.blocks.const import (
    BLOCKS_AGENT_SPEED,
    BLOCKS_PLAYER_SPEED,
    DEFAULT_FALL_INTERVAL_TICKS,
    LINE_CLEAR_COLOR,
    LINE_CLEAR_FLASH_TICKS,
    TETROMINO_COLORS,
    TETROMINOES,
)
from snake.types import Color, Direction, Point


class BlocksGame(BaseGame):
    """
    Block stacking (Tetris-style) game designed for a cylindrical LED screen.
    Operates with 360-degree horizontal wrapping across all columns (x in 0..WIDTH-1),
    random top spawns, penetrable -1 pixels on top, impenetrable -2 pixels on the bottom,
    wall kicks, gravity, line clearing, and hardware rendering.
    """

    def __init__(self) -> None:
        self.grid: dict[Point, Color] = {}
        self.score: int = 0
        self.lines_cleared_total: int = 0
        self.current_shape: str | None = None
        self.current_rotation: int = 0
        self.current_x: int = 0
        self.current_y: int = 0
        self._bag: list[str] = []
        self._game_over: bool = False
        self._gravity_tick_count: int = 0
        self._fall_interval_ticks: int = DEFAULT_FALL_INTERVAL_TICKS
        self._cleared_lines: list[int] = []
        self._line_clear_ticks: int = 0

    @property
    def name(self) -> str:
        return "Blocks"

    @property
    def game_over(self) -> bool:
        return self._game_over

    @game_over.setter
    def game_over(self, value: bool) -> None:
        self._game_over = value

    @property
    def player_speed(self) -> float:
        return BLOCKS_PLAYER_SPEED

    @property
    def agent_speed(self) -> float:
        return BLOCKS_AGENT_SPEED

    def initialize_game(self) -> None:
        """Resets the game state for a new session."""
        self.grid = {}
        self.score = 0
        self.lines_cleared_total = 0
        self.current_shape = None
        self.current_rotation = 0
        self.current_x = 0
        self.current_y = 0
        self._bag = []
        self._game_over = False
        self._gravity_tick_count = 0
        self._fall_interval_ticks = DEFAULT_FALL_INTERVAL_TICKS
        self._cleared_lines = []
        self._line_clear_ticks = 0
        self._spawn_piece()

    def _refill_bag(self) -> None:
        """Refills the random 7-bag generator."""
        shapes = list(TETROMINOES.keys())
        random.shuffle(shapes)
        self._bag = shapes

    def _spawn_piece(self) -> None:
        """Spawns the next tetromino from a random column around the top of the cylinder."""
        if not self._bag:
            self._refill_bag()
        self.current_shape = self._bag.pop()
        self.current_rotation = 0

        # Find all valid spawn positions around the top of the cylinder (y=0)
        valid_xs = [
            x
            for x in range(WIDTH)
            if self._is_valid_position(self.current_shape, x, 0, self.current_rotation)
        ]

        if valid_xs:
            self.current_x = random.choice(valid_xs)
            self.current_y = 0
        else:
            # Cannot spawn anywhere around the top -> topped out / game over
            self.current_x = random.randint(0, WIDTH - 1)
            self.current_y = 0
            self._game_over = True

    def _is_valid_position(self, shape: str | None, x: int, y: int, rotation: int) -> bool:
        """
        Checks if a tetromino can validly occupy position (x, y) with given rotation.
        Wraps horizontally around the cylinder (0 <= px < WIDTH).
        Can pass through -1 pixels on the top, but blocked by -2 impenetrable pixels on the bottom.
        """
        if shape is None or shape not in TETROMINOES:
            return False
        for dx, dy in TETROMINOES[shape][rotation]:
            px = (x + dx) % WIDTH
            py = y + dy
            # Vertical screen bounds
            if py < 0 or py >= HEIGHT:
                return False
            # Impenetrable pixels on the bottom of the screen (-2)
            if led_map.is_impenetrable(px, py):
                return False
            # Existing stacked blocks
            if Point(px, py) in self.grid:
                return False
        return True

    def _move_horizontal(self, dx: int) -> None:
        """Moves the active piece left or right, wrapping around the cylinder."""
        if self.current_shape is None:
            return
        new_x = (self.current_x + dx) % WIDTH
        if self._is_valid_position(
            self.current_shape,
            new_x,
            self.current_y,
            self.current_rotation,
        ):
            self.current_x = new_x

    def _rotate(self) -> None:
        """Rotates the active piece clockwise with cylindrical wall kicks."""
        if self.current_shape is None:
            return
        next_rot = (self.current_rotation + 1) % 4
        # Test current position first, then horizontal/vertical kicks
        kicks = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]
        for kick_x, kick_y in kicks:
            test_x = (self.current_x + kick_x) % WIDTH
            test_y = self.current_y + kick_y
            if self._is_valid_position(
                self.current_shape,
                test_x,
                test_y,
                next_rot,
            ):
                self.current_x = test_x
                self.current_y = test_y
                self.current_rotation = next_rot
                return

    def _drop_step(self) -> None:
        """Drops the active piece by 1 row immediately (soft drop)."""
        if self.current_shape is None:
            return
        if self._is_valid_position(
            self.current_shape,
            self.current_x,
            self.current_y + 1,
            self.current_rotation,
        ):
            self.current_y += 1
            self._gravity_tick_count = 0
        else:
            self._lock_piece()

    def _lock_piece(self) -> None:
        """Locks the active piece into the grid and checks for completed cylinder rings."""
        if self.current_shape is None:
            return
        color = TETROMINO_COLORS[self.current_shape]
        for dx, dy in TETROMINOES[self.current_shape][self.current_rotation]:
            pt = Point((self.current_x + dx) % WIDTH, self.current_y + dy)
            self.grid[pt] = color

        self.current_shape = None

        # Detect full lines (complete rings around playable cells)
        full_lines = []
        for y in range(HEIGHT):
            playable_xs = [x for x in range(WIDTH) if not led_map.is_impenetrable(x, y)]
            if playable_xs and all(Point(x, y) in self.grid for x in playable_xs):
                full_lines.append(y)

        if full_lines:
            self._cleared_lines = full_lines
            self._line_clear_ticks = LINE_CLEAR_FLASH_TICKS
            self.lines_cleared_total += len(full_lines)
            line_scores = [0, 100, 300, 500, 800]
            self.score += line_scores[min(len(full_lines), 4)]
        else:
            self._spawn_piece()

    def _finish_line_clear(self) -> None:
        """
        Collapses full rings and shifts blocks above them down, stopping at
        impenetrable cells.
        """
        if not self._cleared_lines:
            return
        cleared_set = set(self._cleared_lines)
        new_grid: dict[Point, Color] = {}

        # Remove cleared blocks
        surviving = {pt: col for pt, col in self.grid.items() if pt.y not in cleared_set}

        # For each surviving block (from highest y / bottom-most to top),
        # drop it down into cleared rows in its column, stopping if an
        # impenetrable pixel (-2) or another block in new_grid is below it.
        for pt, col in sorted(surviving.items(), key=lambda item: item[0].y, reverse=True):
            new_y = pt.y
            for cy in sorted(self._cleared_lines):
                if (
                    cy > new_y
                    and (new_y + 1 < HEIGHT)
                    and not led_map.is_impenetrable(pt.x, new_y + 1)
                    and Point(pt.x, new_y + 1) not in new_grid
                ):
                    new_y += 1
            new_grid[Point(pt.x, new_y)] = col

        self.grid = new_grid
        self._cleared_lines = []

    def handle_player_input(self, input_data: Any) -> None:
        """Processes player or agent Direction input."""
        if self._game_over or self._line_clear_ticks > 0:
            return

        if isinstance(input_data, Direction):
            if input_data == LEFT:
                self._move_horizontal(-1)
            elif input_data == RIGHT:
                self._move_horizontal(1)
            elif input_data == UP:
                self._rotate()
            elif input_data == DOWN:
                self._drop_step()

    def update_game(self) -> None:
        """Advances game logic by one frame/tick."""
        if self._game_over:
            return

        # Handle line-clearing flash animation
        if self._line_clear_ticks > 0:
            self._line_clear_ticks -= 1
            if self._line_clear_ticks == 0:
                self._finish_line_clear()
                self._spawn_piece()
            return

        # Ensure active piece exists
        if self.current_shape is None:
            self._spawn_piece()
            return

        # Advance gravity counter
        self._gravity_tick_count += 1
        if self._gravity_tick_count >= self._fall_interval_ticks:
            self._gravity_tick_count = 0
            if self._is_valid_position(
                self.current_shape,
                self.current_x,
                self.current_y + 1,
                self.current_rotation,
            ):
                self.current_y += 1
            else:
                self._lock_piece()

    def get_game_state(self) -> dict[Point, Color]:
        """Returns the current visual game state for rendering."""
        state: dict[Point, Color] = {}

        # 1. Locked blocks
        for pt, col in self.grid.items():
            state[pt] = col

        # 2. Line clear flash (flash full rings around the cylinder)
        if self._line_clear_ticks > 0:
            for y in self._cleared_lines:
                for x in range(WIDTH):
                    if not led_map.is_impenetrable(x, y):
                        state[Point(x, y)] = LINE_CLEAR_COLOR
        elif not self._game_over and self.current_shape is not None:
            # 3. Active falling piece wrapped around the cylinder
            color = TETROMINO_COLORS[self.current_shape]
            for dx, dy in TETROMINOES[self.current_shape][self.current_rotation]:
                pt = Point((self.current_x + dx) % WIDTH, self.current_y + dy)
                state[pt] = color

        return state
