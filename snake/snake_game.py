import random

from snake import led_map_v2 as led_map
from snake.const import DIRECTIONS, RIGHT, UP
from snake.types import Direction, Point

WIDTH = len(led_map.MAP[0])  # 14
HEIGHT = len(led_map.MAP)  # 8
INITIAL_SNAKE_LENGTH = 3


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


class SnakeGame:
    def __init__(self):
        self.snake: list[Point] = []
        self.food: Point = None
        self.direction: Direction = RIGHT
        self.game_over: bool = False

    def initialize_game(self):
        self.snake = []
        # Place snake in the middle, starting with INITIAL_SNAKE_LENGTH
        for i in range(INITIAL_SNAKE_LENGTH):
            self.snake.append(Point(WIDTH // 2 - i, HEIGHT // 2))
        self.direction = RIGHT
        self.game_over = False
        self._place_food()

    def _place_food(self):
        # Places food at a random position, ensuring it's not on the snake.
        while True:
            x = random.randint(0, WIDTH - 1)
            y = random.randint(0, HEIGHT - 1)
            if (x, y) not in self.snake and not led_map.is_blocked(x, y):
                self.food = Point(x, y)
                break

    def is_safe(self, point: Point, step: int = 0) -> bool:
        """Checks if a given coordinate is safe (within bounds and not part of the snake body)."""
        if (
            step < len(self.snake)
            and point in self.snake[: len(self.snake) - step]
            or led_map.is_blocked(point.x, point.y)
        ):
            return False
        return True

    def set_next_direction(self, direction: Direction):
        if direction.x == -self.direction.x and direction.y == -self.direction.y:
            return
        self.direction = direction

    @property
    def snake_head(self) -> Point:
        return self.snake[0]

    def update_game(self):

        if self.game_over:
            return
        """Updates the game state for the next frame."""
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
                self.game_over = True
                return
            new_direction = random.choice(possible_directions)
            possible_directions.remove(new_direction)

        direction = new_direction
        new_head = get_next_head(head, direction)
        if new_head in led_map.PORTALS and head in led_map.PORTALS:
            direction = Direction(direction.x, direction.y * -1)

        # Check for self-collision
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)  # Add new head

        # Check if food was eaten
        if new_head == self.food:
            self._place_food()  # Place new food
        else:
            self.snake.pop()  # Remove tail if no food eaten
