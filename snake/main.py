import collections
import enum
import random
import signal

import board
import neopixel_spi as neopixel
import pygame

from snake import led_map_v2 as led_map

# Game configuration
WIDTH = len(led_map.MAP[0])  # 14
HEIGHT = len(led_map.MAP)
INITIAL_SNAKE_LENGTH = 3
PLAYER_GAME_SPEED = 0.15  # Seconds per frame (lower is faster)
AGENT_GAME_SPEED = 0.07  # Seconds per frame (lower is faster)
REFRESH_RATE = 120  # Frames per second
END_SEQUENCE_FLASH_SPEED = 1
END_SEQUENCE_LENGTH = 5

# Types
Direction = collections.namedtuple("Direction", ["x", "y"])
Point = collections.namedtuple("Point", ["x", "y"])
Color = collections.namedtuple("Color", ["g", "r", "b"])

# Color constants
DARK = Color(2, 4, 0)
SNAKE_HEAD = Color(128, 0, 128)
SNAKE_BODY = Color(0, 0, 128)
FOOD = Color(255, 0, 0)

# Direction constants
UP = Direction(0, -1)
DOWN = Direction(0, 1)
LEFT = Direction(-1, 0)
RIGHT = Direction(1, 0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

# Game state variables
snake: list[Point] = []
food: Point = None
direction = RIGHT  # Initial direction
input_direction = RIGHT
game_over = False

# Services Initialization
PIXEL_ORDER = neopixel.GRB
spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(spi, led_map.NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False)
pygame.init()


def clear_screen():
    """Clears the console screen."""
    pixels.fill((0, 0, 0))
    pixels.show()


def initialize_game():
    """Initializes or resets the game state."""
    global snake, direction, game_over

    snake = []
    # Place snake in the middle, starting with INITIAL_SNAKE_LENGTH
    for i in range(INITIAL_SNAKE_LENGTH):
        snake.append((WIDTH // 2 - i, HEIGHT // 2))

    direction = RIGHT
    game_over = False
    place_food()


def place_food():
    """Places food at a random position, ensuring it's not on the snake."""
    global food
    while True:
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        if (x, y) not in snake and not led_map.is_blocked(x, y):
            food = (x, y)
            break


def draw_game(
    snake_head_color: Color = SNAKE_HEAD,
    snake_body_color: Color = SNAKE_BODY,
    food_color: Color = FOOD,
):
    """Draws the game board in the console."""
    matrix = [DARK] * led_map.NUM_PIXELS
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (x, y) == snake[0]:
                matrix[led_map.MAP[y][x]] = snake_head_color  # Snake head
            elif (x, y) in snake:
                matrix[led_map.MAP[y][x]] = snake_body_color  # Snake body
            elif (x, y) == food:
                matrix[led_map.MAP[y][x]] = food_color  # Food

    for i in range(led_map.NUM_PIXELS):
        pixels[i] = matrix[i]
    pixels.show()


def get_next_head(head: Point, direction: Direction) -> Point:
    new_head = Point(head.x + direction.x, head.y + direction.y)
    # Check rotations
    if new_head.x < 0:
        new_head = Point(WIDTH - 1, new_head.y)
    if new_head.x >= WIDTH:
        new_head = Point(0, new_head.y)
    # Check for portals
    if head in led_map.PORTALS and direction == UP:
        new_head = led_map.PORTALS[head]
    return new_head


def update_game():
    """Updates the game state for the next frame."""
    global game_over, direction
    if game_over:
        return

    head = snake[0]
    new_direction = direction
    possible_directions = []
    for directions in set(DIRECTIONS) - {direction}:
        if is_safe(
            get_next_head(head, directions).x,
            get_next_head(head, directions).y,
        ):
            possible_directions.append(directions)
    while (next_head := get_next_head(head, new_direction)) and led_map.is_blocked(
        next_head.x, next_head.y
    ):
        if len(possible_directions) == 0:
            game_over = True
            return
        new_direction = random.choice(possible_directions)
        possible_directions.remove(new_direction)

    direction = new_direction
    new_head = get_next_head(head, direction)
    if new_head in led_map.PORTALS and head in led_map.PORTALS:
        direction = Direction(direction.x, direction.y * -1)

    # Check for self-collision
    if new_head in snake:
        game_over = True
        return

    snake.insert(0, new_head)  # Add new head

    # Check if food was eaten
    if new_head == food:
        place_food()  # Place new food
    else:
        snake.pop()  # Remove tail if no food eaten


def is_safe(point: Point, step=0):
    """Checks if a given coordinate is safe (within bounds and not part of the snake body)."""
    # Check self-collision
    # For a simple check, we just ensure it's not in the current snake body.
    # A more advanced agent might consider the snake's future state.
    if (
        step < len(snake)
        and point in snake[: len(snake) - step]
        or led_map.is_blocked(point.x, point.y)
    ):
        return False  # Otherwise, it's part of the snake body
    return True


def agent_move():
    """
    Determines the next move for the AI agent.
    Simple greedy strategy: move towards food, avoid immediate collisions.

    WARNING: This is a simple greedy strategy and does not consider the
    snake's future state, wrapping around the map or portals.
    """
    global direction
    head = snake[0]
    food_x, food_y = food

    # Prioritize moves that reduce distance to food
    possible_moves_with_distances = []

    for dir in DIRECTIONS:
        next_head = get_next_head(head, dir)

        # Avoid reversing directly into the snake's body
        if len(snake) > 1 and next_head == snake[1]:
            continue

        if is_safe(next_head):
            distance = abs(next_head.x - food_x) + abs(next_head.y - food_y)
            possible_moves_with_distances.append((distance, dir))

    # Sort moves by distance (ascending)
    possible_moves_with_distances.sort()

    # Try to pick the best safe move
    for _, dir in possible_moves_with_distances:
        # The is_safe check here is crucial.
        # We need to ensure the *wrapped* next_x, next_y is safe.
        # The is_safe function itself now only checks for self-collision.
        if is_safe(get_next_head(head, dir)):
            direction = dir
            return

    # Fallback: if no 'best' move is found (e.g., trapped), try any safe move
    # This part should ideally be unreachable with a good
    # 'is_safe' and 'possible_moves_with_distances'
    # but acts as a safeguard.
    for dir in DIRECTIONS:
        # Again, apply wrapping before checking safety
        if is_safe(get_next_head(head, dir)):
            direction = dir
            return

    # If absolutely no safe move is found (snake is completely trapped),
    # the game will end on the next update_game() call due to collision.
    # For the agent, this means it has no valid move.
    # In a real game, this might trigger a specific "stuck" state or game over.
    # Here, we just let the game_over logic handle it.


def agent_move_bfs():
    global direction

    head = snake[0]
    if head == food:
        return
    queue = [(head, [head])]
    visited = set()
    while queue:
        head, path = queue.pop(0)
        if head in visited:
            continue
        visited.add(head)
        if head == food:
            direction = Direction(path[1].x - path[0].x, path[1].y - path[0].y)
            return
        for dir in DIRECTIONS:
            next_head = get_next_head(head, dir)
            if is_safe(next_head, len(path) - 1) and next_head not in visited:
                queue.append((next_head, path + [next_head]))
    # If no path is found, snake will go in a safe direction until it finds food
    agent_move()


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
        if hat_x == -1 and direction != RIGHT:
            input_direction = LEFT
        elif hat_x == 1 and direction != LEFT:
            input_direction = RIGHT
        elif hat_y == 1 and direction != DOWN:
            input_direction = UP
        elif hat_y == -1 and direction != UP:
            input_direction = DOWN
    else:
        # Fall back to analog stick (axes)
        x_axis = joystick.get_axis(0)
        y_axis = joystick.get_axis(1)
        if abs(x_axis) > abs(y_axis):
            if x_axis < -0.5 and direction != RIGHT:
                input_direction = LEFT
            elif x_axis > 0.5 and direction != LEFT:
                input_direction = RIGHT
        else:
            if y_axis < -0.5 and direction != DOWN:
                input_direction = UP
            elif y_axis > 0.5 and direction != UP:
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
    def __init__(self, init_time_ms: int):
        self.init_time_ms = init_time_ms
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
            (i, 0, i),
            (0, 0, i),
            FOOD,
        )


def game_loop():
    """Main game loop."""
    global direction

    initialize_game()
    game_mode = GameMode.AGENT
    last_update_tick = pygame.time.get_ticks()
    end_sequence = None
    input_direction = None
    game_clock = pygame.time.Clock()

    while True:
        if not game_over:
            if (
                game_mode == GameMode.AGENT
                and pygame.time.get_ticks() - last_update_tick >= AGENT_GAME_SPEED * 1000
            ):
                agent_move_bfs()
                update_game()
                draw_game()
                last_update_tick = pygame.time.get_ticks()
            elif game_mode == GameMode.PLAYER:
                if (tmp_dir := handle_joystick_direction()) is not None:
                    input_direction = tmp_dir
                if pygame.time.get_ticks() - last_update_tick >= PLAYER_GAME_SPEED * 1000:
                    if input_direction is not None:
                        direction = input_direction
                        input_direction = None
                    update_game()
                    draw_game()
                    last_update_tick = pygame.time.get_ticks()
        else:
            if end_sequence is None:
                last_update_tick = pygame.time.get_ticks()
                end_sequence = EndSequence(last_update_tick)
            end_sequence.draw_frame(pygame.time.get_ticks())
            if end_sequence.done:
                initialize_game()
                end_sequence = None
                last_update_tick = pygame.time.get_ticks()

        req_game_mode = handle_joystick_game_mode()
        if req_game_mode != game_mode and req_game_mode is not None:
            game_mode = req_game_mode
            initialize_game()
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
    except Exception as e:
        clear_screen()
        print(f"An error occurred: {e}")
        print("Exiting game.")


if __name__ == "__main__":
    main()
