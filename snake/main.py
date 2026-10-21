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


GAMES: list[tuple[str, BaseGame, Callable[[Any], Direction | None]]] = [
    ("snake", snake_game.SnakeGame(), snake_agent_move_bfs),
    ("blocks", blocks_game.BlocksGame(), blocks_agent_move),
]


def game_loop() -> None:
    """Main game loop."""
    _, game, agent = random.choice(GAMES)

    game.initialize_game()

    game_mode = GameMode.AGENT
    last_update_tick = pygame.time.get_ticks()
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
            renderer.draw(game.get_game_state())
        else:
            if renderer.end_game_effect(game.get_game_state()):
                _, game, agent = random.choice(GAMES)
                game.initialize_game()
                last_update_tick = pygame.time.get_ticks()

        req_game_mode = handle_joystick_game_mode()
        if req_game_mode != game_mode and req_game_mode is not None:
            game_mode = req_game_mode
            game.initialize_game()
            renderer.reset_end_game_effect()
            last_update_tick = pygame.time.get_ticks()
            continue

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
