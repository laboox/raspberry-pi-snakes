from __future__ import annotations

import signal
import sys
from typing import Any

import pygame

from snake import led_map_v2 as led_map
from snake.const import (
    BLOCKED,
    DARK,
    DOWN,
    END_SEQUENCE_FLASH_SPEED,
    END_SEQUENCE_LENGTH,
    HEIGHT,
    LEFT,
    PORTALS,
    REFRESH_RATE,
    RIGHT,
    SCALE,
    SNAKE_DANCE_MODE,
    UP,
    WIDTH,
    GameMode,
)
from snake.games.base_game import BaseGame
from snake.games.snake import snake_game
from snake.games.snake.agent import snake_agent_move_bfs
from snake.types import Color, Direction, Point

if SNAKE_DANCE_MODE == "RASPBERRYPI":
    try:
        import board
        import neopixel_spi as neopixel
    except (ImportError, NotImplementedError):
        board = None
        neopixel = None
        SNAKE_DANCE_MODE = "DESKTOP"

# Initializations
pygame.init()
if SNAKE_DANCE_MODE == "RASPBERRYPI":
    # Services Initialization
    PIXEL_ORDER = neopixel.GRB
    spi = board.SPI()
    pixels = neopixel.NeoPixel_SPI(
        spi, led_map.NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False
    )
    screen = None
else:
    pixels = None
    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))


def clear_screen() -> None:
    if SNAKE_DANCE_MODE == "RASPBERRYPI" and pixels is not None:
        pixels.fill((0, 0, 0))
        pixels.show()
    elif screen is not None:
        screen.fill((0, 0, 0))
        pygame.display.flip()


def draw_game(game: BaseGame, opacity: float = 1.0) -> None:
    """Draws the current game state from the game class to the display."""
    game_state = game.get_game_state()

    factor = opacity / 255.0 if opacity > 1.0 else max(0.0, min(1.0, opacity))

    if factor != 1.0:
        rendered_state = {
            point: Color(
                int(color.g * factor),
                int(color.r * factor),
                int(color.b * factor),
            )
            for point, color in game_state.items()
        }
    else:
        rendered_state = game_state

    if SNAKE_DANCE_MODE == "RASPBERRYPI":
        if pixels is None:
            return
        pixels.fill(DARK)
        for point, color in rendered_state.items():
            if 0 <= point.y < HEIGHT and 0 <= point.x < WIDTH:
                pixel_idx = led_map.MAP[point.y][point.x]
                if pixel_idx != -1:
                    pixels[pixel_idx] = color
        pixels.show()
    else:
        if screen is None:
            return
        screen.fill(DARK)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                point = Point(x, y)
                if led_map.is_blocked(x, y):
                    pygame.draw.rect(screen, BLOCKED, (x * SCALE, y * SCALE, SCALE, SCALE))
                elif point in led_map.PORTALS and point in PORTALS:
                    pygame.draw.circle(
                        screen,
                        PORTALS[point],
                        (x * SCALE + SCALE / 2, y * SCALE + SCALE / 2),
                        SCALE / 2,
                    )
        for point, color in rendered_state.items():
            pygame.draw.rect(screen, color, (point.x * SCALE, point.y * SCALE, SCALE, SCALE))
        pygame.display.flip()


def handle_joystick_direction() -> Direction | None:
    if pygame.joystick.get_count() == 0:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            return LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            return RIGHT
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            return UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            return DOWN
        return None

    joystick = pygame.joystick.Joystick(0)
    # Use the hat (D-pad) instead of axes for direction
    hat_x, hat_y = joystick.get_hat(0)
    if hat_x != 0 or hat_y != 0:
        # Use hat (D-pad) input if available
        if hat_x == -1:
            return LEFT
        elif hat_x == 1:
            return RIGHT
        elif hat_y == 1:
            return UP
        elif hat_y == -1:
            return DOWN
    else:
        # Fall back to analog stick (axes)
        x_axis = joystick.get_axis(0)
        y_axis = joystick.get_axis(1)
        if abs(x_axis) > abs(y_axis):
            if x_axis < -0.5:
                return LEFT
            elif x_axis > 0.5:
                return RIGHT
        else:
            if y_axis < -0.5:
                return UP
            elif y_axis > 0.5:
                return DOWN
    return None


def handle_joystick_game_mode() -> GameMode | None:
    if pygame.joystick.get_count() == 0:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_1]:
            return GameMode.PLAYER
        if keys[pygame.K_2]:
            return GameMode.AGENT
        if keys[pygame.K_3]:
            return GameMode.ML_AGENT
        return None

    joystick = pygame.joystick.Joystick(0)
    if joystick.get_button(7):
        return GameMode.PLAYER
    if joystick.get_button(6):
        return GameMode.AGENT
    return None


class EndSequence:
    def __init__(self, init_time_ms: int, game: BaseGame):
        self.init_time_ms = init_time_ms
        self.game = game
        self.done = False

    def draw_frame(self, time_ms: int) -> None:
        if time_ms - self.init_time_ms > END_SEQUENCE_LENGTH * 1000:
            self.done = True
        if self.done:
            return
        elapsed = (time_ms - self.init_time_ms) * 255 * 2 * END_SEQUENCE_FLASH_SPEED / 1000
        i = abs(int(elapsed) % (255 * 2) - 255)
        draw_game(self.game, opacity=i / 255.0)


def game_loop(game: BaseGame | None = None) -> None:
    """Main game loop."""
    if game is None:
        game = snake_game.SnakeGame()
        agent = snake_agent_move_bfs

    game.initialize_game()

    game_mode = GameMode.PLAYER
    last_update_tick = pygame.time.get_ticks()
    end_sequence: EndSequence | None = None
    input_direction: Direction | None = None
    game_clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()

        if not game.game_over:
            update_interval = (
                game.agent_speed * 1000
                if game_mode in (GameMode.AGENT, GameMode.ML_AGENT)
                else game.player_speed * 1000
            )

            if game_mode in (GameMode.AGENT, GameMode.ML_AGENT):
                if pygame.time.get_ticks() - last_update_tick >= update_interval:
                    agent_dir = agent(game)
                    game.handle_player_input(agent_dir)
                    game.update_game()
                    draw_game(game)
                    last_update_tick = pygame.time.get_ticks()
            elif game_mode == GameMode.PLAYER:
                if (tmp_dir := handle_joystick_direction()) is not None:
                    input_direction = tmp_dir
                if pygame.time.get_ticks() - last_update_tick >= update_interval:
                    if input_direction is not None:
                        game.handle_player_input(input_direction)
                        input_direction = None
                    game.update_game()
                    draw_game(game)
                    last_update_tick = pygame.time.get_ticks()
        else:
            if end_sequence is None:
                last_update_tick = pygame.time.get_ticks()
                end_sequence = EndSequence(last_update_tick, game)
            end_sequence.draw_frame(pygame.time.get_ticks())
            if end_sequence.done:
                game.initialize_game()
                end_sequence = None
                last_update_tick = pygame.time.get_ticks()

        req_game_mode = handle_joystick_game_mode()
        if req_game_mode != game_mode and req_game_mode is not None:
            game_mode = req_game_mode
            game.initialize_game()
            end_sequence = None
            last_update_tick = pygame.time.get_ticks()
            continue

        game_clock.tick(REFRESH_RATE)


def exit_game(signum: int | None = None, frame: Any = None) -> None:
    clear_screen()
    sys.exit(0)


def main() -> None:
    """Entry point for the snake game."""
    signal.signal(signal.SIGTERM, exit_game)
    try:
        game_loop()
    except SystemExit:
        clear_screen()
        print("Thanks for playing Snake!")


if __name__ == "__main__":
    main()
