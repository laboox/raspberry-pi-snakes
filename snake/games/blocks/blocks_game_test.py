from __future__ import annotations

import unittest

from snake import led_map_v2 as led_map
from snake.const import DOWN, LEFT, RIGHT, UP, WIDTH
from snake.games.blocks.agent import blocks_agent_move
from snake.games.blocks.blocks_game import BlocksGame
from snake.games.blocks.const import (
    LINE_CLEAR_COLOR,
    LINE_CLEAR_FLASH_TICKS,
    TETROMINO_COLORS,
    TETROMINOES,
)
from snake.types import Color, Point


class TestBlocksGame(unittest.TestCase):
    def setUp(self) -> None:
        self.game = BlocksGame()
        self.game.initialize_game()

    def test_initialization(self) -> None:
        self.assertEqual(self.game.name, "Blocks")
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.lines_cleared_total, 0)
        self.assertIsNotNone(self.game.current_shape)
        self.assertIn(self.game.current_shape, TETROMINOES)
        self.assertEqual(self.game.current_rotation, 0)
        self.assertEqual(len(self.game.grid), 0)

    def test_penetrable_minus_one_on_top(self) -> None:
        # At (0, 0), MAP is -1 (missing LED on top)
        self.assertEqual(led_map.MAP[0][0], -1)
        # Pieces can move through -1 on the top
        self.assertTrue(self.game._is_valid_position("O", 0, 0, 0))

    def test_impenetrable_minus_two_on_bottom(self) -> None:
        # At (0, 8), MAP is -2 (impenetrable pixel on bottom)
        self.assertEqual(led_map.MAP[8][0], -2)
        self.assertTrue(led_map.is_impenetrable(0, 8))

        # "O" piece has height 2 (dy: 0, 1).
        # At y=7, its blocks are at y=7 and y=8 -> should be INVALID because y=8 is -2
        self.assertFalse(self.game._is_valid_position("O", 0, 7, 0))

        # At y=6, its blocks are at y=6 and y=7 -> both are valid
        self.assertTrue(self.game._is_valid_position("O", 0, 6, 0))

    def test_stacking_on_top_of_impenetrable_pixels(self) -> None:
        # Position "O" piece in column 0 at y=6 (above the -2 floor at row 8)
        self.game.current_shape = "O"
        self.game.current_rotation = 0
        self.game.current_x = 0
        self.game.current_y = 6

        # Trying to drop step cannot move to y=7 (because y=8 is -2), so it locks on top of row 8
        self.game.handle_player_input(DOWN)
        self.assertEqual(len(self.game.grid), 4)
        # Blocks should be locked at y=6 and y=7 in columns 0 and 1
        self.assertIn(Point(0, 6), self.game.grid)
        self.assertIn(Point(0, 7), self.game.grid)
        self.assertIn(Point(1, 6), self.game.grid)
        self.assertIn(Point(1, 7), self.game.grid)

    def test_horizontal_movement_and_cylindrical_wrapping(self) -> None:
        self.game.current_shape = "O"
        self.game.current_rotation = 0
        self.game.current_x = 0
        self.game.current_y = 2

        # Move left from 0 wraps to WIDTH - 1 (13)
        self.game.handle_player_input(LEFT)
        self.assertEqual(self.game.current_x, WIDTH - 1)

        # Move right from WIDTH - 1 wraps back to 0
        self.game.handle_player_input(RIGHT)
        self.assertEqual(self.game.current_x, 0)

    def test_piece_spanning_cylinder_seam(self) -> None:
        # At x = WIDTH - 1 (13), an "O" piece spans columns 13 and 0
        self.game.current_shape = "O"
        self.game.current_rotation = 0
        self.game.current_x = WIDTH - 1
        self.game.current_y = 2

        state = self.game.get_game_state()
        self.assertIn(Point(WIDTH - 1, 2), state)
        self.assertIn(Point(0, 2), state)
        self.assertIn(Point(WIDTH - 1, 3), state)
        self.assertIn(Point(0, 3), state)

    def test_random_spawns_around_top(self) -> None:
        spawn_xs = set()
        for _ in range(30):
            self.game.initialize_game()
            self.assertEqual(self.game.current_y, 0)
            self.assertGreaterEqual(self.game.current_x, 0)
            self.assertLess(self.game.current_x, WIDTH)
            spawn_xs.add(self.game.current_x)

        # Over 30 spawns, pieces should spawn across multiple different columns
        self.assertGreater(len(spawn_xs), 1)

    def test_line_clear_full_ring(self) -> None:
        # Row 7 has all 14 columns playable. Fill almost completely leaving columns 12, 13 for "O"
        test_color = Color(10, 20, 30)
        for x in range(WIDTH - 2):
            self.game.grid[Point(x, 7)] = test_color

        self.game.current_shape = "O"
        self.game.current_rotation = 0
        self.game.current_x = WIDTH - 2
        self.game.current_y = 6  # Blocks at y=6 and y=7

        # Drop to lock
        self.game.handle_player_input(DOWN)

        # Full ring on row 7 detected -> line clear animation starts
        self.assertGreater(self.game.lines_cleared_total, 0)
        self.assertGreater(self.game.score, 0)
        self.assertEqual(self.game._line_clear_ticks, LINE_CLEAR_FLASH_TICKS)

        # Row 7 should flash
        state = self.game.get_game_state()
        for x in range(WIDTH):
            self.assertEqual(state[Point(x, 7)], LINE_CLEAR_COLOR)

        # Advance frames to complete clear animation
        for _ in range(LINE_CLEAR_FLASH_TICKS):
            self.game.update_game()
        self.assertEqual(self.game._line_clear_ticks, 0)

    def test_line_clear_does_not_overwrite_blocks_above_impenetrable_floor(self) -> None:
        # Row 8 has playable columns 3..10 and impenetrable (-2) at column 0.
        # Place two stacked blocks in column 0 at y=6 (top_color) and y=7 (bottom_color),
        # deliberately inserting y=6 first into the dict.
        top_color = Color(10, 20, 30)
        bottom_color = Color(40, 50, 60)
        self.game.grid[Point(0, 6)] = top_color
        self.game.grid[Point(0, 7)] = bottom_color

        # Also place a block above a playable column at (3, 7)
        falling_color = Color(70, 80, 90)
        self.game.grid[Point(3, 7)] = falling_color

        # Fill row 8 across all playable columns (3..10) and trigger line clear collapse
        for x in range(3, 11):
            self.game.grid[Point(x, 8)] = Color(100, 100, 100)
        self.game._cleared_lines = [8]
        self.game._finish_line_clear()

        # In column 0, (0, 8) is impenetrable (-2), so (0, 7) cannot fall and
        # (0, 6) must not overwrite (0, 7).
        self.assertEqual(self.game.grid.get(Point(0, 7)), bottom_color)
        self.assertEqual(self.game.grid.get(Point(0, 6)), top_color)
        # In column 3, (3, 8) was cleared and is playable, so (3, 7) falls to (3, 8).
        self.assertEqual(self.game.grid.get(Point(3, 8)), falling_color)
        self.assertNotIn(Point(3, 7), self.game.grid)

    def test_game_over(self) -> None:
        # Fill the entire top row with blocks
        for x in range(WIDTH):
            for y in range(2):
                self.game.grid[Point(x, y)] = Color(100, 100, 100)

        # Attempt to spawn piece when top is completely full
        self.game._spawn_piece()
        self.assertTrue(self.game.game_over)

    def test_get_game_state(self) -> None:
        state = self.game.get_game_state()
        self.assertIsInstance(state, dict)
        active_blocks = [
            Point((self.game.current_x + dx) % WIDTH, self.game.current_y + dy)
            for dx, dy in TETROMINOES[self.game.current_shape][self.game.current_rotation]
        ]
        for pt in active_blocks:
            self.assertIn(pt, state)
            self.assertEqual(state[pt], TETROMINO_COLORS[self.game.current_shape])

    def test_agent_move(self) -> None:
        move = blocks_agent_move(self.game)
        self.assertIn(move, [LEFT, RIGHT, UP, DOWN, None])


if __name__ == "__main__":
    unittest.main()
