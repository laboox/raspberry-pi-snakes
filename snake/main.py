import collections
import enum
import random
import time

import board
import neopixel_spi as neopixel
import pygame

from snake import led_map_v2 as led_map

# if os.getenv("AS_SERVICE", None) is not None:
#     import systemd

#     AS_SERVICE = True
# else:
#     AS_SERVICE = False

# Game configuration
WIDTH = len(led_map.MAP[0])  # 14
HEIGHT = len(led_map.MAP)
INITIAL_SNAKE_LENGTH = 3
PLAYER_GAME_SPEED = 0.2  # Seconds per frame (lower is faster)
AGENT_GAME_SPEED = 0.07  # Seconds per frame (lower is faster)
REFRESH_RATE = 60  # Frames per second
END_SEQUENCE_FLASH_SPEED = 1
END_SEQUENCE_LENGTH = 5

DARK = (2, 4, 0)
SNAKE_HEAD = (128, 0, 128)
SNAKE_BODY = (0, 0, 128)
FOOD = (255, 0, 0)

# Directions
Direction = collections.namedtuple("Direction", ["x", "y"])
Point = collections.namedtuple("Point", ["x", "y"])

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
score = 0
game_over = False

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
    global snake, direction, score, game_over

    snake = []
    # Place snake in the middle, starting with INITIAL_SNAKE_LENGTH
    for i in range(INITIAL_SNAKE_LENGTH):
        snake.append((WIDTH // 2 - i, HEIGHT // 2))

    direction = RIGHT
    score = 0
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


def draw_game(snake_head_color=SNAKE_HEAD, snake_body_color=SNAKE_BODY, food_color=FOOD):
    """Draws the game board in the console."""
    # print(f"Score: {score}")
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


def get_next_head(head, direction):
    new_head = (head[0] + direction[0], head[1] + direction[1])
    # Check rotations
    if new_head[0] < 0:
        new_head = (WIDTH - 1, new_head[1])
    if new_head[0] >= WIDTH:
        new_head = (0, new_head[1])
    # Check for portals
    if head in led_map.PORTALS and direction == UP:
        new_head = led_map.PORTALS[head]
    return new_head


def update_game():
    """Updates the game state for the next frame."""
    global score, game_over, direction
    if game_over:
        return

    head_x, head_y = snake[0]
    new_direction = direction
    possible_directions = []
    for directions in set(DIRECTIONS) - {direction}:
        if is_safe(
            get_next_head(snake[0], directions)[0],
            get_next_head(snake[0], directions)[1],
        ):
            possible_directions.append(directions)
    while (next_head := get_next_head(snake[0], new_direction)) and led_map.is_blocked(
        next_head[0], next_head[1]
    ):
        if len(possible_directions) == 0:
            game_over = True
            return
        new_direction = random.choice(possible_directions)
        possible_directions.remove(new_direction)

    direction = new_direction
    new_head = get_next_head(snake[0], direction)
    if new_head in led_map.PORTALS and (head_x, head_y) in led_map.PORTALS:
        direction = (direction[0], direction[1] * -1)

    # Check for self-collision
    if new_head in snake:
        game_over = True
        return

    snake.insert(0, new_head)  # Add new head

    # Check if food was eaten
    if new_head == food:
        score += 1
        place_food()  # Place new food
    else:
        snake.pop()  # Remove tail if no food eaten


def is_safe(x, y, step=0):
    """Checks if a given coordinate is safe (within bounds and not part of the snake body)."""
    # Check self-collision
    # For a simple check, we just ensure it's not in the current snake body.
    # A more advanced agent might consider the snake's future state.
    if (step < len(snake) and (x, y) in snake[: len(snake) - step]) or led_map.is_blocked(x, y):
        return False  # Otherwise, it's part of the snake body
    return True


def agent_move():
    """
    Determines the next move for the AI agent.
    Simple greedy strategy: move towards food, avoid immediate collisions.
    """
    global direction
    head_x, head_y = snake[0]
    food_x, food_y = food

    # Prioritize moves that reduce distance to food
    possible_moves_with_distances = []

    for dx, dy in DIRECTIONS:
        next_x, next_y = get_next_head(snake[0], (dx, dy))

        # Avoid reversing directly into the snake's body
        if len(snake) > 1 and (next_x, next_y) == snake[1]:
            continue

        if is_safe(next_x, next_y):
            distance = abs(next_x - food_x) + abs(next_y - food_y)
            possible_moves_with_distances.append((distance, (dx, dy)))

    # Sort moves by distance (ascending)
    possible_moves_with_distances.sort()

    # Try to pick the best safe move
    for _, (dx, dy) in possible_moves_with_distances:
        # The is_safe check here is crucial.
        # We need to ensure the *wrapped* next_x, next_y is safe.
        # The is_safe function itself now only checks for self-collision.
        if is_safe((head_x + dx) % WIDTH, (head_y + dy) % HEIGHT):
            direction = (dx, dy)
            return

    # Fallback: if no 'best' move is found (e.g., trapped), try any safe move
    # This part should ideally be unreachable with a good
    # 'is_safe' and 'possible_moves_with_distances'
    # but acts as a safeguard.
    for dx, dy in DIRECTIONS:
        # Again, apply wrapping before checking safety
        if is_safe((head_x + dx) % WIDTH, (head_y + dy) % HEIGHT):
            direction = (dx, dy)
            return

    # If absolutely no safe move is found (snake is completely trapped),
    # the game will end on the next update_game() call due to collision.
    # For the agent, this means it has no valid move.
    # In a real game, this might trigger a specific "stuck" state or game over.
    # Here, we just let the game_over logic handle it.


def agent_move_bfs():
    global direction

    head_x, head_y = snake[0]
    if snake[0] == food:
        return
    queue = [(head_x, head_y, [(head_x, head_y)])]
    visited = set()
    while queue:
        x, y, path = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        if (x, y) == food:
            direction = (path[1][0] - path[0][0], path[1][1] - path[0][1])
            return
        for dx, dy in DIRECTIONS:
            next_x, next_y = get_next_head((x, y), (dx, dy))
            if is_safe(next_x, next_y, len(path) - 1) and (next_x, next_y) not in visited:
                queue.append((next_x, next_y, path + [(next_x, next_y)]))
    # If no path is found, snake will go in a safe direction until it finds food
    agent_move()
    return


def print_snake():
    for x, y in reversed(snake):
        print(f"({x}, {y})", end=" ")
    print()


class GameMode(enum.StrEnum):
    AGENT = "agent"
    PLAYER = "player"


def handle_joystick_direction() -> Direction | None:
    input_direction = None
    # # Use pygame joystick to read the direction
    # for event in pygame.event.get(pump=True):
    #     if event.type == pygame.JOYDEVICEADDED:
    #         pygame.joystick.Joystick(event.device_index).init()
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


def end_sequence():
    # Draw the game with snake flashing a few times
    for i in range(5):
        for i in list(range(255)) + list(range(255, 0, -1)):
            draw_game((0, 0, i), (0, 0, i), (0, 0, 0))
            time.sleep(END_SEQUENCE_FLASH_SPEED / (255 * 2))

    # Draw the game with snake flashing a few times
    print("Game over")


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
            (0, 0, i),
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


def main():
    """Entry point for the snake game."""
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
