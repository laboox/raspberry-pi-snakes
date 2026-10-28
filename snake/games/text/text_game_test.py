from __future__ import annotations

import unittest

from snake import led_map_v2 as led_map
from snake.const import WIDTH
from snake.games.text.const import (
    CHAR_HEIGHT,
    CHAR_SPACING,
    CHAR_WIDTH,
    DEFAULT_TEXT_COLOR,
    FONT_3X5,
    TEXT_AGENT_SPEED,
    TEXT_PLAYER_SPEED,
    TEXT_START_Y,
)
from snake.games.text.text_game import TextGame
from snake.types import Color, Point


class TestTextGame(unittest.TestCase):
    def setUp(self) -> None:
        self.game = TextGame("HI")
        self.game.initialize_game()

    def test_initialization_and_properties(self) -> None:
        self.assertEqual(self.game.name, "Text")
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.current_x, WIDTH - 1)
        self.assertEqual(self.game.player_speed, TEXT_PLAYER_SPEED)
        self.assertEqual(self.game.agent_speed, TEXT_AGENT_SPEED)
        # "HI" -> 2 chars * 3 width + 1 spacing = 7 pixels wide
        self.assertEqual(self.game.text_width, 7)

    def test_font_dimensions_and_playable_rows(self) -> None:
        for ch, glyph in FONT_3X5.items():
            self.assertEqual(len(glyph), CHAR_HEIGHT, f"Bad height for '{ch}'")
            for row in glyph:
                self.assertEqual(len(row), CHAR_WIDTH, f"Bad width for '{ch}'")
                self.assertTrue(set(row).issubset({"#", "."}))

        # Verify rows 3..7 have no impenetrable (-2) LEDs across all columns
        for y in range(TEXT_START_Y, TEXT_START_Y + CHAR_HEIGHT):
            for x in range(WIDTH):
                self.assertFalse(led_map.is_impenetrable(x, y))

    def test_first_character_starts_at_far_right_of_screen(self) -> None:
        game = TextGame("I")
        game.initialize_game()
        state = game.get_game_state()

        right_x = WIDTH - 1
        # Leftmost column of "I" is at x = WIDTH - 1, top/bottom rows are "#"
        self.assertIn(Point(right_x, TEXT_START_Y), state)
        self.assertIn(Point(right_x, TEXT_START_Y + CHAR_HEIGHT - 1), state)
        # Only column WIDTH - 1 is on screen initially
        self.assertTrue(all(pt.x == right_x for pt in state))

    def test_scrolling_until_last_character_exits_screen(self) -> None:
        # "HI" has text_width = 7, starting at x = WIDTH - 1 (13).
        # Last pixel of "I" starts at x = 13 + 7 - 1 = 19.
        # After 19 ticks, current_x = -6, last pixel of "I" is at x = 0.
        for _ in range(WIDTH - 1 + self.game.text_width - 1):
            self.game.update_game()
            self.assertFalse(self.game.game_over)

        # Last character's rightmost column is now at x = 0
        self.assertEqual(self.game.current_x + self.game.text_width - 1, 0)
        state_at_left_edge = self.game.get_game_state()
        self.assertTrue(any(pt.x == 0 for pt in state_at_left_edge))

        # One more tick shifts the last character completely off screen (x < 0)
        self.game.update_game()
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.get_game_state(), {})

        # Further updates when game_over do not change current_x
        final_x = self.game.current_x
        self.game.update_game()
        self.assertEqual(self.game.current_x, final_x)

    def test_no_wrapping_for_long_text(self) -> None:
        game = TextGame("HELLO WORLD")
        game.initialize_game()
        state = game.get_game_state()

        # First character starts at WIDTH - 1 (13), so columns 0..12 are empty
        for pt in state:
            self.assertEqual(pt.x, WIDTH - 1)
            self.assertGreaterEqual(pt.y, TEXT_START_Y)
            self.assertLess(pt.y, TEXT_START_Y + CHAR_HEIGHT)

    def test_set_text_and_empty_text(self) -> None:
        self.game.set_text("")
        self.assertEqual(self.game.text_width, 0)
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.get_game_state(), {})

        self.game.set_text("a?")
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.current_x, WIDTH - 1)
        self.assertEqual(self.game.text_width, 2 * CHAR_WIDTH + CHAR_SPACING)

    def test_custom_color_and_unknown_character_fallback(self) -> None:
        custom_color = Color(10, 20, 30)
        game = TextGame("@", color=custom_color)
        game.initialize_game()
        state = game.get_game_state()
        self.assertGreater(len(state), 0)
        for col in state.values():
            self.assertEqual(col, custom_color)

    def test_game_over_setter(self) -> None:
        self.game.game_over = True
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.color, DEFAULT_TEXT_COLOR)


if __name__ == "__main__":
    unittest.main()
