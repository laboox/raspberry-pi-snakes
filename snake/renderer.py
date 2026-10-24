from __future__ import annotations

from typing import Any

import pygame

from snake import led_map_v2 as led_map
from snake.const import (
    BLOCKED,
    DARK,
    END_SEQUENCE_LENGTH,
    HEIGHT,
    PORTALS,
    SCALE,
    SNAKE_DANCE_MODE,
    WIDTH,
)
from snake.games.base_game import BaseGame
from snake.types import Color, Effect, Point


class Renderer:
    """
    Renders game states to the display (either Raspberry Pi NeoPixel SPI or Desktop Pygame).
    Supports rendering arbitrary game states, opacity blending, clearing,
    synchronized pixel flashing effects, and end-game animation sequences.
    """

    def __init__(
        self,
        mode: str | None = None,
        screen: pygame.Surface | None = None,
        pixels: Any | None = None,
        scale: int = SCALE,
        flash_interval_ms: int = 500,
    ) -> None:
        self.mode = mode or SNAKE_DANCE_MODE
        self.scale = scale
        self.screen = screen
        self.pixels = pixels
        self.flash_interval_ms = flash_interval_ms
        self._flash_start_time: int | None = None
        self._end_effect_start_time: int | None = None

        if self.screen is None and self.pixels is None:
            self._init_display()

    def _init_display(self) -> None:
        """Initializes display hardware or pygame window based on configured mode."""
        pygame.init()
        if self.mode == "RASPBERRYPI":
            try:
                import board
                import neopixel_spi as neopixel

                spi = board.SPI()
                self.pixels = neopixel.NeoPixel_SPI(
                    spi,
                    led_map.NUM_PIXELS,
                    pixel_order=neopixel.GRB,
                    auto_write=False,
                )
                self.screen = None
            except (ImportError, NotImplementedError):
                self.pixels = None
                self.mode = "DESKTOP"
                self.screen = pygame.display.set_mode((WIDTH * self.scale, HEIGHT * self.scale))
        else:
            self.pixels = None
            self.screen = pygame.display.set_mode((WIDTH * self.scale, HEIGHT * self.scale))

    def clear(self) -> None:
        """Clears the display buffer to solid black."""
        self._flash_start_time = None
        if self.mode == "RASPBERRYPI" and self.pixels is not None:
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
        elif self.screen is not None:
            self.screen.fill((0, 0, 0))
            pygame.display.flip()

    def reset_flash_effect(self) -> None:
        """Resets the internal timer for pixel flash effects."""
        self._flash_start_time = None

    def draw(
        self,
        game_or_state: dict[Point, Color] | BaseGame,
        opacity: float = 1.0,
    ) -> None:
        """
        Draws the given game state (or extracts it from a BaseGame instance) to the display.
        Supports opacity factor for animations and fade effects.
        Automatically detects pixels with flashing effects, managing a synchronized flash timer.
        """
        if isinstance(game_or_state, BaseGame):
            game_state = game_or_state.get_game_state()
        else:
            game_state = game_or_state

        factor = opacity / 255.0 if opacity > 1.0 else max(0.0, min(1.0, opacity))

        if factor != 1.0:
            rendered_state = {
                point: Color(
                    int(color.g * factor),
                    int(color.r * factor),
                    int(color.b * factor),
                    effect=getattr(color, "effect", Effect.NONE),
                )
                for point, color in game_state.items()
            }
        else:
            rendered_state = game_state

        has_flash_pixels = any(
            getattr(color, "effect", Effect.NONE) == Effect.FLASH
            for color in rendered_state.values()
        )

        if has_flash_pixels:
            current_time = pygame.time.get_ticks()

            if self._flash_start_time is None:
                self._flash_start_time = current_time

            elapsed_ms = current_time - self._flash_start_time
            flash_factor = elapsed_ms * 255 * 2 / self.flash_interval_ms
            flash_factor = abs(int(flash_factor) % (255 * 2) - 255) / 255
        else:
            self._flash_start_time = None
            flash_factor = 1

        if self.mode == "RASPBERRYPI":
            if self.pixels is None:
                return
            self.pixels.fill(DARK[:3])
            for point, color in rendered_state.items():
                if 0 <= point.y < HEIGHT and 0 <= point.x < WIDTH:
                    pixel_idx = led_map.MAP[point.y][point.x]
                    if pixel_idx >= 0:
                        is_flash = color.effect == Effect.FLASH
                        rgb = (
                            (color.g, color.r, color.b)
                            if not is_flash
                            else (
                                color.g * flash_factor,
                                color.r * flash_factor,
                                color.b * flash_factor,
                            )
                        )
                        self.pixels[pixel_idx] = rgb
            self.pixels.show()
        else:
            if self.screen is None:
                return
            self.screen.fill(DARK[:3])
            for point, color in rendered_state.items():
                rgb = (
                    (color.r, color.g, color.b)
                    if getattr(color, "effect", Effect.NONE) != Effect.FLASH
                    else (
                        color.r * flash_factor,
                        color.g * flash_factor,
                        color.b * flash_factor,
                    )
                )
                pygame.draw.rect(
                    self.screen,
                    rgb,
                    (point.x * self.scale, point.y * self.scale, self.scale, self.scale),
                )
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    point = Point(x, y)
                    if led_map.is_blocked(x, y):
                        pygame.draw.rect(
                            self.screen,
                            BLOCKED[:3],
                            (x * self.scale, y * self.scale, self.scale, self.scale),
                        )
                    elif point in led_map.PORTALS and point in PORTALS:
                        pygame.draw.circle(
                            self.screen,
                            PORTALS[point][:3],
                            (
                                x * self.scale + self.scale / 2,
                                y * self.scale + self.scale / 2,
                            ),
                            self.scale / 2,
                        )
            pygame.display.flip()

    def reset_end_game_effect(self) -> None:
        """Resets the internal timer for the end-game effect."""
        self._end_effect_start_time = None

    def end_game_effect(
        self,
        game_or_state: dict[Point, Color] | BaseGame,
        time_ms: int | None = None,
        init_time_ms: int | None = None,
        opacity: float = 1.0,
    ) -> bool:
        """
        Renders the end-game flashing sequence on the given game state.
        Returns True when the end sequence is completed, False while ongoing.
        """
        if time_ms is None:
            time_ms = pygame.time.get_ticks()

        if init_time_ms is not None:
            start_time = init_time_ms
        else:
            if self._end_effect_start_time is None:
                self._end_effect_start_time = time_ms
            start_time = self._end_effect_start_time

        if time_ms - start_time > END_SEQUENCE_LENGTH * 1000:
            self._end_effect_start_time = None
            return True

        if isinstance(game_or_state, BaseGame):
            game_state = game_or_state.get_game_state()
        else:
            game_state = game_or_state
        flashing_state = {
            point: Color(
                int(color.g),
                int(color.r),
                int(color.b),
                effect=Effect.FLASH,
            )
            for point, color in game_state.items()
        }

        self.draw(flashing_state, opacity=opacity)
        return False
