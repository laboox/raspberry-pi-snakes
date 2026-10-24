from __future__ import annotations

import random
from typing import Any

from snake import led_map_v2 as led_map
from snake.const import DIRECTIONS, HEIGHT, RIGHT, UP, WIDTH
from snake.games.base_game import BaseGame
from snake.games.snake.const import (
    AGENT_GAME_SPEED,
    FOOD,
    INITIAL_SNAKE_LENGTH,
    PLAYER_GAME_SPEED,
    SNAKE_BODY,
    SNAKE_HEAD,
)
from snake.types import Color, Direction, Point


def get_next_head(head: Point, direction: Direction) -> Point:
    new_head = Point(head.x + direction.x, head.y + direction.y)
    # Check rotations
    if new_head.x < 0:
        new_head = Point(WIDTH - 1, new_head.y)
    if new_head.x >= WIDTH:
        new_head = Point(0, new_head.y)
    # Check for portals
    if head in led_map.PORTALS and direction == UP:
        new_head = Point(*led_map.PORTALS[head])
    return new_head


class SnakeGame(BaseGame):
    def __init__(self) -> None:
        self.snake: list[Point] = []
        self.food: Point | None = None
        self.direction: Direction = RIGHT
        self._game_over: bool = False

    @property
    def name(self) -> str:
        return "Snake"

    @property
    def game_over(self) -> bool:
        return self._game_over

    @game_over.setter
    def game_over(self, value: bool) -> None:
        self._game_over = value

    def initialize_game(self) -> None:
        self.snake = []
        # Place snake in the middle, starting with INITIAL_SNAKE_LENGTH
        for i in range(INITIAL_SNAKE_LENGTH):
            self.snake.append(Point(WIDTH // 2 - i, HEIGHT // 2))
        self.direction = RIGHT
        self._game_over = False
        self._place_food()

    def _place_food(self) -> None:
        # Places food at a random position, ensuring it's not on the snake.
        while True:
            x = random.randint(0, WIDTH - 1)
            y = random.randint(0, HEIGHT - 1)
            if (x, y) not in self.snake and not led_map.is_blocked(x, y):
                self.food = Point(x, y)
                break

    def is_safe(self, point: Point, step: int = 0) -> bool:
        """Checks if a given coordinate is safe (within bounds and not part of snake body)."""
        if (
            step < len(self.snake)
            and point in self.snake[: len(self.snake) - step]
            or led_map.is_blocked(point.x, point.y)
        ):
            return False
        return True

    def set_next_direction(self, direction: Direction) -> None:
        if direction.x == -self.direction.x and direction.y == -self.direction.y:
            return
        self.direction = direction

    @property
    def snake_head(self) -> Point | None:
        return self.snake[0] if self.snake else None

    def update_game(self) -> None:
        if self._game_over:
            return
        """Updates the game state for the next frame."""
        if not self.snake:
            return

        head = self.snake[0]
        new_direction = self.direction
        possible_directions = []
        for directions in set[Direction](DIRECTIONS) - {self.direction}:  # type: ignore
            if self.is_safe(get_next_head(head, directions)):
                possible_directions.append(directions)
        while (next_head := get_next_head(head, new_direction)) and led_map.is_blocked(
            next_head.x, next_head.y
        ):
            if len(possible_directions) == 0:
                self._game_over = True
                return
            new_direction = random.choice(possible_directions)
            possible_directions.remove(new_direction)

        self.direction = new_direction
        new_head = get_next_head(head, self.direction)
        if new_head in led_map.PORTALS and head in led_map.PORTALS and self.direction == UP:
            self.direction = Direction(self.direction.x, self.direction.y * -1)

        # Check for self-collision
        if new_head in self.snake:
            self._game_over = True
            return

        self.snake.insert(0, new_head)  # Add new head

        # Check if food was eaten
        if new_head == self.food:
            self._place_food()  # Place new food
        else:
            self.snake.pop()  # Remove tail if no food eaten

    def get_game_state(self) -> dict[Point, Color]:
        """Returns the current visual game state as a mapping of points to colors."""
        state: dict[Point, Color] = {}
        if self.food is not None:
            state[self.food] = FOOD
        for part in self.snake:
            state[part] = SNAKE_BODY
        if self.snake_head is not None:
            state[self.snake_head] = SNAKE_HEAD
        return state

    def handle_player_input(self, input_data: Any) -> None:
        if isinstance(input_data, Direction):
            self.set_next_direction(input_data)

    @property
    def player_speed(self) -> float:
        """Player frame interval in seconds (lower is faster)."""
        return PLAYER_GAME_SPEED

    @property
    def agent_speed(self) -> float:
        """Agent frame interval in seconds (lower is faster)."""
        return AGENT_GAME_SPEED
