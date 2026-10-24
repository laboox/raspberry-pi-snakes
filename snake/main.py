from __future__ import annotations

import random
import signal
import sys
from collections.abc import Callable
from typing import Any

import pygame

from snake.const import DOWN, LEFT, REFRESH_RATE, RIGHT, UP, GameMode
from snake.games.base_game import BaseGame
from snake.games.blocks import blocks_game
from snake.games.blocks.agent import blocks_agent_move
from snake.games.snake import snake_game
from snake.games.snake.agent import snake_agent_move_bfs
from snake.renderer import Renderer
from snake.types import Direction

renderer = Renderer()

# Keep the Joystick object alive: pygame closes the device when it is garbage
# collected. On Linux (Raspberry Pi) a freshly opened joystick only learns button
# state from evdev events that arrive after opening, so re-opening it every frame
# means buttons always read as released. macOS polls values directly, so it hid this.
_joystick: pygame.joystick.JoystickType | None = None


def get_joystick() -> pygame.joystick.JoystickType | None:
    global _joystick
    if pygame.joystick.get_count() == 0:
        _joystick = None
    elif _joystick is None:
        _joystick = pygame.joystick.Joystick(0)
    return _joystick


def get_start_back_buttons(joystick: pygame.joystick.JoystickType) -> tuple[int, int]:
    """Returns (start, back) button indices for the given controller."""
    if "Dual Action" in joystick.get_name():
        # Logitech Dual Action (DirectInput layout)
        return 9, 8
    # XInput / Xbox layout, e.g. Logitech Gamepad F310 in X mode on the Raspberry Pi
    return 7, 6


def handle_joystick_direction() -> Direction | None:
    joystick = get_joystick()
    if joystick is not None and (direction := _joystick_direction(joystick)) is not None:
        return direction

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


def _joystick_direction(joystick: pygame.joystick.JoystickType) -> Direction | None:
    # Use the hat (D-pad) instead of axes for direction
    hat_x, hat_y = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0, 0)
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
    elif joystick.get_numaxes() >= 2:
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


def handle_joystick_game_mode() -> [GameMode, str | None] | None:
    joystick = get_joystick()
    if joystick is not None:
        start_button, back_button = get_start_back_buttons(joystick)
        if joystick.get_button(start_button):
            if joystick.get_button(5):
                return GameMode.PLAYER, "Blocks"
            return GameMode.PLAYER, "Snake"
        if joystick.get_button(back_button):
            if joystick.get_button(5):
                return GameMode.AGENT, "Blocks"
            return GameMode.AGENT, "Snake"

    keys = pygame.key.get_pressed()
    if keys[pygame.K_1]:
        return GameMode.PLAYER, "Snake"
    if keys[pygame.K_2]:
        return GameMode.AGENT, "Snake"
    return None, None


def handle_joystick_opacity_change() -> float | None:
    joystick = get_joystick()
    if joystick is not None:
        if joystick.get_button(4):
            if joystick.get_axis(5) > 0.5:
                return 0.2
            elif joystick.get_axis(2) > 0.5:
                return -0.2
    return 0


GAMES: list[tuple[BaseGame, Callable[[Any], Direction | None]]] = [
    (snake_game.SnakeGame(), snake_agent_move_bfs),
    (blocks_game.BlocksGame(), blocks_agent_move),
]


def game_loop() -> None:
    """Main game loop."""
    game, agent = random.choice(GAMES)

    game.initialize_game()

    game_mode = GameMode.AGENT
    last_update_tick = pygame.time.get_ticks()
    input_direction: Direction | None = None
    game_clock = pygame.time.Clock()

    default_opacity = 0.6
    old_opacity_change = 0

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
                    last_update_tick = pygame.time.get_ticks()
            elif game_mode == GameMode.PLAYER:
                if (tmp_dir := handle_joystick_direction()) is not None:
                    input_direction = tmp_dir
                if pygame.time.get_ticks() - last_update_tick >= update_interval:
                    if input_direction is not None:
                        game.handle_player_input(input_direction)
                        input_direction = None
                    game.update_game()
                    last_update_tick = pygame.time.get_ticks()
            renderer.draw(game.get_game_state(), opacity=default_opacity)
        else:
            if renderer.end_game_effect(game.get_game_state(), opacity=default_opacity):
                game, agent = random.choice(GAMES)
                game.initialize_game()
                last_update_tick = pygame.time.get_ticks()

        req_game_mode, game_name = handle_joystick_game_mode()
        if (req_game_mode is not None and req_game_mode != game_mode) or (
            game_name is not None and game.name != game_name
        ):
            for g, a in GAMES:
                if g.name == game_name:
                    game = g
                    agent = a
            game_mode = req_game_mode
            game.initialize_game()
            renderer.reset_end_game_effect()
            last_update_tick = pygame.time.get_ticks()
            continue
        opacity_diff = handle_joystick_opacity_change()
        if opacity_diff != 0 and opacity_diff != old_opacity_change:
            default_opacity = min(default_opacity + opacity_diff, 1.0)
            default_opacity = max(default_opacity, 0.1)
        old_opacity_change = opacity_diff

        game_clock.tick(REFRESH_RATE)


def exit_game(signum: int | None = None, frame: Any = None) -> None:
    renderer.clear()
    sys.exit(0)


def main() -> None:
    """Entry point for the game."""
    signal.signal(signal.SIGTERM, exit_game)
    try:
        game_loop()
    except SystemExit:
        renderer.clear()
        print("Thanks for playing!")


if __name__ == "__main__":
    main()
