import random
import time

import board
import neopixel_spi as neopixel
import pygame

from snake.led_map import MAP, PORTALS

# Game configuration
WIDTH = len(MAP[0])
HEIGHT = len(MAP)
INITIAL_SNAKE_LENGTH = 3
GAME_SPEED = 0.1  # Seconds per frame (lower is faster)
REFRESH_RATE = 1 / 30  # Frames per second

DARK = (0, 5, 0)
SNAKE_HEAD = (128, 0, 128)
SNAKE_BODY = (0, 0, 128)
FOOD = (255, 0, 0)

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

# Game state variables
snake = []
food = ()
direction = RIGHT  # Initial direction
input_direction = RIGHT
score = 0
game_over = False
new_food = False

NUM_PIXELS = 100
PIXEL_ORDER = neopixel.GRB
spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(spi, NUM_PIXELS, pixel_order=PIXEL_ORDER, auto_write=False)
pygame.init()


def clear_screen():
    """Clears the console screen."""
    pass


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
        if (x, y) not in snake and MAP[y][x] != -1:
            food = (x, y)
            break


def draw_game(snake_head_color=SNAKE_HEAD, snake_body_color=SNAKE_BODY, food_color=FOOD):
    """Draws the game board in the console."""
    clear_screen()
    # print(f"Score: {score}")
    matrix = [DARK] * NUM_PIXELS
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (x, y) == snake[0]:
                matrix[MAP[y][x]] = snake_head_color  # Snake head
            elif (x, y) in snake:
                matrix[MAP[y][x]] = snake_body_color  # Snake body
            elif (x, y) == food:
                matrix[MAP[y][x]] = food_color  # Food

    for i in range(NUM_PIXELS):
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
    if head in PORTALS and direction == UP:
        new_head = PORTALS[head]
    return new_head


def update_game():
    """Updates the game state for the next frame."""
    global score, game_over, direction, new_food
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
    while (
        MAP[get_next_head(snake[0], new_direction)[1]][get_next_head(snake[0], new_direction)[0]]
        == -1
    ):
        if len(possible_directions) == 0:
            game_over = True
            return
        new_direction = random.choice(possible_directions)
        possible_directions.remove(new_direction)

    direction = new_direction
    new_head = get_next_head(snake[0], direction)
    if new_head in PORTALS and (head_x, head_y) in PORTALS:
        direction = (direction[0], direction[1] * -1)

    # Check for self-collision
    if new_head in snake:
        game_over = True
        return

    snake.insert(0, new_head)  # Add new head

    # Check if food was eaten
    if new_head == food:
        score += 1
        new_food = True
        place_food()  # Place new food
    else:
        snake.pop()  # Remove tail if no food eaten


def is_safe(x, y):
    """Checks if a given coordinate is safe (within bounds and not part of the snake body)."""
    # Check self-collision
    # For a simple check, we just ensure it's not in the current snake body.
    # A more advanced agent might consider the snake's future state.
    if (x, y) in snake or MAP[y][x] == -1:
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
    for dist, (dx, dy) in possible_moves_with_distances:
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
    global direction, new_food

    head_x, head_y = snake[0]
    food_x, food_y = food
    if snake[0] == food:
        return
    queue = [(head_x, head_y, [(head_x, head_y)])]
    visited = set()
    visited.add((head_x, head_y))
    while queue:
        x, y, path = queue.pop(0)
        visited.add((x, y))
        if (x, y) == food:
            direction = (path[1][0] - path[0][0], path[1][1] - path[0][1])
            if new_food:
                new_food = False
            return
        for dx, dy in DIRECTIONS:
            next_x, next_y = get_next_head((x, y), (dx, dy))
            if is_safe(next_x, next_y) and (next_x, next_y) not in visited:
                queue.append((next_x, next_y, path + [(next_x, next_y)]))
    # If no path is found, snake will go in a safe direction until it finds food
    agent_move()
    return


def print_snake():
    for x, y in reversed(snake):
        print(f"({x}, {y})", end=" ")
    print()


def handle_joystick_sync():
    global input_direction
    # Use pygame joystick to read the direction
    for event in pygame.event.get(pump=True):
        if event.type == pygame.JOYDEVICEADDED:
            pygame.joystick.Joystick(event.device_index).init()
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


def handle_joystick_events():
    global direction

    for event in pygame.event.get(pump=True):
        if event.type == pygame.JOYDEVICEADDED:
            pygame.joystick.Joystick(event.device_index).init()
        if event.type == pygame.JOYAXISMOTION:
            x_axis = event.joy.get_axis(0)
            y_axis = event.joy.get_axis(1)
            if abs(x_axis) > abs(y_axis):
                if x_axis < -0.5 and direction != RIGHT:
                    direction = LEFT
                elif x_axis > 0.5 and direction != LEFT:
                    direction = RIGHT
            else:
                if y_axis < -0.5 and direction != UP:
                    direction = UP
                elif y_axis > 0.5 and direction != DOWN:
                    direction = DOWN


def end_sequence():
    # Draw the game with snake flashing a few times
    for i in range(5):
        for i in list(range(255)) + list(range(255, 0, -1)):
            draw_game((0, 0, i), (0, 0, i), (0, 0, 0))
            time.sleep(1 / 500)

    # Draw the game with snake flashing a few times
    print("Game over")


def game_loop():
    """Main game loop."""
    # global direction, input_direction

    initialize_game()
    while True:
        agent_move_bfs()
        if not game_over:
            update_game()
        else:
            end_sequence()
            initialize_game()
        draw_game()
        time.sleep(GAME_SPEED)
        # start_time = time.time()
        # frame_time = 0
        # input_direction = direction
        # while time.time() - start_time < GAME_SPEED:
        #     handle_joystick_sync()
        #     time.sleep(REFRESH_RATE)
        # direction = input_direction


if __name__ == "__main__":
    try:
        game_loop()
    except SystemExit:
        clear_screen()
        print("Thanks for playing Snake!")
    except Exception as e:
        clear_screen()
        print(f"An error occurred: {e}")
        print("Exiting game.")
