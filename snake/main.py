import enum
import os
import random
import signal

import pygame

from snake import led_map_v2 as led_map
from snake import snake_game
from snake.const import DIRECTIONS, DOWN, LEFT, RIGHT, UP
from snake.types import Color, Direction, Point

SNAKE_DANCE_MODE = os.environ.get("SNAKE_DANCE_MODE", "RASPBERRYPI")

if SNAKE_DANCE_MODE == "RASPBERRYPI":
    import board
    import neopixel_spi as neopixel


# Game configuration
WIDTH = len(led_map.MAP[0])  # 14
HEIGHT = len(led_map.MAP)  # 8
INITIAL_SNAKE_LENGTH = 3
PLAYER_GAME_SPEED = 0.15  # Seconds per frame (lower is faster)
AGENT_GAME_SPEED = 0.07  # Seconds per frame (lower is faster)
REFRESH_RATE = 30  # Frames per second
END_SEQUENCE_FLASH_SPEED = 1
END_SEQUENCE_LENGTH = 5

# Color constants
DARK = Color(2, 4, 0)
SNAKE_HEAD = Color(128, 0, 128)
SNAKE_BODY = Color(0, 0, 128)
FOOD = Color(255, 0, 0)
BLOCKED = Color(0, 255, 0)
PORTALS = {}
for portal in led_map.PORTALS.keys():
    color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    if PORTALS.get(portal) is None:
        PORTALS[portal] = color
        PORTALS[led_map.PORTALS[portal]] = color

# Initializations
pygame.init()
if SNAKE_DANCE_MODE == "RASPBERRYPI":
    # Services Initialization
    PIXEL_ORDER = neopixel.GRB
    spi = board.SPI()
    pixels = neopixel.NeoPixel_SPI(
        spi, led_map.NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False
    )
else:
    SCALE = 50
    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))


def clear_screen():
    if SNAKE_DANCE_MODE == "RASPBERRYPI":
        pixels.fill((0, 0, 0))
        pixels.show()
    else:
        screen.fill((0, 0, 0))
        pygame.display.flip()


def draw_game(
    game: snake_game.SnakeGame,
    snake_head_color: Color = SNAKE_HEAD,
    snake_body_color: Color = SNAKE_BODY,
    food_color: Color = FOOD,
):
    if SNAKE_DANCE_MODE == "RASPBERRYPI":
        """Draws the game board in the console."""
        pixels.fill(DARK)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                point = Point(x, y)
                if point == game.snake_head:
                    pixels[led_map.MAP[y][x]] = snake_head_color  # Snake head
                elif point in game.snake:
                    pixels[led_map.MAP[y][x]] = snake_body_color  # Snake body
                elif point == game.food:
                    pixels[led_map.MAP[y][x]] = food_color  # Food

        pixels.show()
    else:
        screen.fill(DARK)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                point = Point(x, y)
                if point == game.snake_head:
                    pygame.draw.rect(screen, snake_head_color, (x * SCALE, y * SCALE, SCALE, SCALE))
                elif point in game.snake:
                    pygame.draw.rect(screen, snake_body_color, (x * SCALE, y * SCALE, SCALE, SCALE))
                elif point == game.food:
                    pygame.draw.rect(screen, food_color, (x * SCALE, y * SCALE, SCALE, SCALE))
                elif led_map.is_blocked(x, y):
                    pygame.draw.rect(screen, BLOCKED, (x * SCALE, y * SCALE, SCALE, SCALE))
                elif led_map.PORTALS.get(point) is not None:
                    pygame.draw.circle(
                        screen,
                        PORTALS[point],
                        (x * SCALE + SCALE / 2, y * SCALE + SCALE / 2),
                        SCALE / 2,
                    )
        pygame.display.flip()


def agent_move(game: snake_game.SnakeGame) -> Direction | None:
    """
    Determines the next move for the AI agent.
    Simple greedy strategy: move towards food, avoid immediate collisions.

    WARNING: This is a simple greedy strategy and does not consider the
    snake's future state, wrapping around the map or portals.
    """
    head = game.snake_head
    food_x, food_y = game.food.x, game.food.y

    # Prioritize moves that reduce distance to food
    possible_moves_with_distances = []

    for dir in DIRECTIONS:
        next_head = snake_game.get_next_head(head, dir)

        # Avoid reversing directly into the snake's body
        if len(game.snake) > 1 and next_head == game.snake[1]:
            continue

        if game.is_safe(next_head):
            distance = abs(next_head.x - food_x) + abs(next_head.y - food_y)
            possible_moves_with_distances.append((distance, dir))

    # Sort moves by distance (ascending)
    possible_moves_with_distances.sort()

    # Try to pick the best safe move
    for _, dir in possible_moves_with_distances:
        # The is_safe check here is crucial.
        # We need to ensure the *wrapped* next_x, next_y is safe.
        # The is_safe function itself now only checks for self-collision.
        if game.is_safe(snake_game.get_next_head(head, dir)):
            return dir

    # Fallback: if no 'best' move is found (e.g., trapped), try any safe move
    # This part should ideally be unreachable with a good
    # 'is_safe' and 'possible_moves_with_distances'
    # but acts as a safeguard.
    for dir in DIRECTIONS:
        # Again, apply wrapping before checking safety
        if game.is_safe(snake_game.get_next_head(head, dir)):
            return dir

    # If absolutely no safe move is found (snake is completely trapped),
    # the game will end on the next update_game() call due to collision.
    # For the agent, this means it has no valid move.
    # In a real game, this might trigger a specific "stuck" state or game over.
    # Here, we just let the game_over logic handle it.


def agent_move_bfs(game: snake_game.SnakeGame) -> Direction | None:

    head = game.snake_head
    if head == game.food:
        return None
    queue: list[tuple[Point, list[Point]]] = [(head, [head])]
    visited = set()
    while queue:
        head, path = queue.pop(0)
        if head in visited:
            continue
        visited.add(head)
        if head == game.food:
            return Direction(path[1].x - path[0].x, path[1].y - path[0].y)
        for dir in DIRECTIONS:
            next_head = snake_game.get_next_head(head, dir)
            if game.is_safe(next_head, len(path) - 1) and next_head not in visited:
                queue.append((next_head, path + [next_head]))
    # If no path is found, snake will go in a safe direction until it finds food
    return agent_move(game)


class GameMode(enum.StrEnum):
    AGENT = "agent"
    PLAYER = "player"


def handle_joystick_direction() -> Direction | None:
    input_direction = None
    if pygame.joystick.get_count() == 0:
        return  # Wait for joystick to be connected
    joystick = pygame.joystick.Joystick(0)
    # Use the hat (D-pad) instead of axes for direction
    hat_x, hat_y = joystick.get_hat(0)
    if hat_x != 0 or hat_y != 0:
        # Use hat (D-pad) input if available
        if hat_x == -1:
            input_direction = LEFT
        elif hat_x == 1:
            input_direction = RIGHT
        elif hat_y == 1:
            input_direction = UP
        elif hat_y == -1:
            input_direction = DOWN
    else:
        # Fall back to analog stick (axes)
        x_axis = joystick.get_axis(0)
        y_axis = joystick.get_axis(1)
        if abs(x_axis) > abs(y_axis):
            if x_axis < -0.5:
                input_direction = LEFT
            elif x_axis > 0.5:
                input_direction = RIGHT
        else:
            if y_axis < -0.5:
                input_direction = UP
            elif y_axis > 0.5:
                input_direction = DOWN
    return input_direction


def handle_joystick_game_mode() -> GameMode | None:
    if pygame.joystick.get_count() == 0:
        return  # Wait for joystick to be connected
    joystick = pygame.joystick.Joystick(0)

    if joystick.get_button(7):
        return GameMode.PLAYER
    if joystick.get_button(6):
        return GameMode.AGENT
    return None


class EndSequence:
    def __init__(self, init_time_ms: int, game: snake_game.SnakeGame):
        self.init_time_ms = init_time_ms
        self.game = game
        self.done = False

    def draw_frame(self, time_ms: int):
        if time_ms - self.init_time_ms > END_SEQUENCE_LENGTH * 1000:
            self.done = True
        if self.done:
            return
        i = abs(
            ((time_ms - self.init_time_ms) * 255 * 2 * END_SEQUENCE_FLASH_SPEED / 1000) % (255 * 2)
            - 255
        )
        draw_game(
            self.game,
            (i, 0, i),
            (0, 0, i),
            FOOD,
        )


def game_loop():
    """Main game loop."""

    game = snake_game.SnakeGame()

    game.initialize_game()

    game_mode = GameMode.AGENT
    last_update_tick = pygame.time.get_ticks()
    end_sequence = None
    input_direction = None
    game_clock = pygame.time.Clock()

    while True:
        pygame.event.pump()
        if not game.game_over:
            if (
                game_mode == GameMode.AGENT
                and pygame.time.get_ticks() - last_update_tick >= AGENT_GAME_SPEED * 1000
            ):
                if (tmp_dir := agent_move_bfs(game)) is not None:
                    game.set_next_direction(tmp_dir)
                game.update_game()
                draw_game(game)
                last_update_tick = pygame.time.get_ticks()
            elif game_mode == GameMode.PLAYER:
                if (tmp_dir := handle_joystick_direction()) is not None:
                    input_direction = tmp_dir
                if pygame.time.get_ticks() - last_update_tick >= PLAYER_GAME_SPEED * 1000:
                    if input_direction is not None:
                        game.set_next_direction(input_direction)
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


def exit_game():
    clear_screen()
    exit(0)


def main():
    """Entry point for the snake game."""
    signal.signal(signal.SIGTERM, exit_game)
    try:
        game_loop()
    except SystemExit:
        clear_screen()
        print("Thanks for playing Snake!")


if __name__ == "__main__":
    main()
