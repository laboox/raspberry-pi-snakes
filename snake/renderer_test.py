from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame  # noqa: E402

from snake import led_map_v2 as led_map  # noqa: E402
from snake.const import DARK, END_SEQUENCE_LENGTH, HEIGHT, SCALE, WIDTH  # noqa: E402
from snake.games.base_game import BaseGame  # noqa: E402
from snake.renderer import Renderer  # noqa: E402
from snake.types import Color, Effect, Point  # noqa: E402


class DummyGame(BaseGame):
    def __init__(self) -> None:
        self._game_over = False

    @property
    def game_over(self) -> bool:
        return self._game_over

    def initialize_game(self) -> None:
        self._game_over = False

    def update_game(self) -> None:
        pass

    def get_game_state(self) -> dict[Point, Color]:
        return {
            Point(5, 5): Color(10, 20, 30),
            Point(6, 5): Color(40, 50, 60),
        }


class TestRenderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def setUp(self) -> None:
        self.screen = pygame.Surface((WIDTH * SCALE, HEIGHT * SCALE))
        self.renderer = Renderer(mode="DESKTOP", screen=self.screen, scale=SCALE)

    def test_initialization(self) -> None:
        self.assertEqual(self.renderer.mode, "DESKTOP")
        self.assertEqual(self.renderer.scale, SCALE)
        self.assertEqual(self.renderer.screen, self.screen)
        self.assertIsNone(self.renderer.pixels)

    def test_clear_screen(self) -> None:
        with patch("pygame.display.flip"):
            self.renderer.clear()
            # Top-left pixel should be black
            self.assertEqual(self.screen.get_at((0, 0))[:3], (0, 0, 0))

    def test_draw_with_game_state_dict(self) -> None:
        game_state = {
            Point(1, 1): Color(100, 150, 200),
            Point(2, 2): Color(50, 60, 70),
        }
        with patch("pygame.display.flip") as mock_flip:
            self.renderer.draw(game_state)
            mock_flip.assert_called_once()

    def test_draw_with_base_game_instance(self) -> None:
        game = DummyGame()
        with patch("pygame.display.flip") as mock_flip:
            self.renderer.draw(game)
            mock_flip.assert_called_once()

    def test_draw_with_opacity(self) -> None:
        game_state = {
            Point(1, 1): Color(100, 200, 50),
        }
        with patch("pygame.display.flip"):
            self.renderer.draw(game_state, opacity=0.5)

    def test_color_effect_dimension(self) -> None:
        # Default effect is Effect.NONE
        c1 = Color(10, 20, 30)
        self.assertEqual(c1.effect, Effect.NONE)

        # Explicit flash effect
        c2 = Color(255, 255, 255, Effect.FLASH)
        self.assertEqual(c2.effect, Effect.FLASH)

        c3 = Color(255, 255, 255, effect=Effect.FLASH)
        self.assertEqual(c3.effect, Effect.FLASH)

    def test_flash_pixels_timer_and_simultaneous_flashing(self) -> None:
        # Two flash pixels in the game state
        game_state = {
            Point(1, 1): Color(255, 255, 255, Effect.FLASH),
            Point(2, 1): Color(255, 255, 255, Effect.FLASH),
            Point(3, 1): Color(100, 150, 200, Effect.NONE),
        }

        with patch("pygame.display.flip"):
            # First frame with flash pixel at t=1000ms -> initializes timer, phase is ON
            self.renderer.draw(game_state, time_ms=1000)
            self.assertEqual(self.renderer._flash_start_time, 1000)

            # At t=1100ms (100ms elapsed with default 100ms interval) -> phase is OFF
            self.renderer.draw(game_state, time_ms=1100)
            self.assertEqual(self.renderer._flash_start_time, 1000)

            # At t=1200ms (200ms elapsed) -> phase is ON again
            self.renderer.draw(game_state, time_ms=1200)
            self.assertEqual(self.renderer._flash_start_time, 1000)

            # Once flash pixels are removed -> timer is cleared
            no_flash_state = {Point(3, 1): Color(100, 150, 200)}
            self.renderer.draw(no_flash_state, time_ms=1300)
            self.assertIsNone(self.renderer._flash_start_time)

    def test_end_game_effect_progression_and_completion(self) -> None:
        game_state = {Point(3, 3): Color(255, 0, 0)}
        with patch("pygame.display.flip"):
            # Start of sequence at t = 1000
            done = self.renderer.end_game_effect(game_state, time_ms=1000)
            self.assertFalse(done)

            # Mid-sequence at t = 2000
            done = self.renderer.end_game_effect(game_state, time_ms=2000)
            self.assertFalse(done)

            # Past END_SEQUENCE_LENGTH seconds (e.g. 1000 + 5001 = 6001)
            finish_time = 1000 + int(END_SEQUENCE_LENGTH * 1000) + 100
            done = self.renderer.end_game_effect(game_state, time_ms=finish_time)
            self.assertTrue(done)

    def test_reset_end_game_effect(self) -> None:
        game_state = {Point(1, 1): Color(100, 100, 100)}
        with patch("pygame.display.flip"):
            self.renderer.end_game_effect(game_state, time_ms=1000)
            self.assertIsNotNone(self.renderer._end_effect_start_time)
            self.renderer.reset_end_game_effect()
            self.assertIsNone(self.renderer._end_effect_start_time)

    def test_raspberry_pi_mode_mock(self) -> None:
        mock_pixels = MagicMock()
        r_pi = Renderer(mode="RASPBERRYPI", pixels=mock_pixels)
        self.assertEqual(r_pi.mode, "RASPBERRYPI")

        game_state = {Point(5, 5): Color(10, 20, 30)}
        r_pi.draw(game_state)
        mock_pixels.fill.assert_called_with((DARK.g, DARK.r, DARK.b))
        mock_pixels.show.assert_called_once()

    def test_raspberry_pi_mode_flash_pixel(self) -> None:
        mock_pixels = MagicMock()
        r_pi = Renderer(mode="RASPBERRYPI", pixels=mock_pixels, flash_interval_ms=100)
        flash_state = {Point(5, 5): Color(255, 255, 255, Effect.FLASH)}

        # Phase ON (t=0)
        r_pi.draw(flash_state, time_ms=0)
        pixel_idx = led_map.MAP[5][5]
        mock_pixels.__setitem__.assert_called_with(pixel_idx, (255, 255, 255))

        # Phase OFF (t=100)
        r_pi.draw(flash_state, time_ms=100)
        mock_pixels.__setitem__.assert_called_with(pixel_idx, (DARK.g, DARK.r, DARK.b))


if __name__ == "__main__":
    unittest.main()
