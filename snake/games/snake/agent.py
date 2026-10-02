from snake.const import DIRECTIONS
from snake.games.snake import snake_game
from snake.types import Direction, Point


def snake_agent_move(game: snake_game.SnakeGame) -> Direction | None:
    """
    Determines the next move for the snake AI agent using a greedy heuristic.
    Simple greedy strategy: move towards food, avoid immediate collisions.

    WARNING: This is a simple greedy strategy and does not consider the
    snake's future state, wrapping around the map or portals.
    """
    head = game.snake_head
    if head is None or game.food is None:
        return None
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
    return None


def snake_agent_move_bfs(game: snake_game.SnakeGame) -> Direction | None:
    """Determines the next move for the snake AI agent using BFS shortest path."""
    head = game.snake_head
    if head is None or game.food is None or head == game.food:
        return None
    queue: list[tuple[Point, Direction, int]] = [(head, Direction(0, 0), 0)]
    visited = set()
    while queue:
        head, start_dir, steps = queue.pop(0)
        if head in visited:
            continue
        visited.add(head)
        if head == game.food:
            return start_dir
        for dir in DIRECTIONS:
            next_head = snake_game.get_next_head(head, dir)
            if game.is_safe(next_head, steps) and next_head not in visited:
                queue.append(
                    (next_head, dir if start_dir == Direction(0, 0) else start_dir, steps + 1)
                )
    # If no path is found, snake will go in a safe direction until it finds food
    return snake_agent_move(game)
