from __future__ import annotations

from typing import Any

from snake import led_map_v2 as led_map
from snake.const import DOWN, HEIGHT, LEFT, RIGHT, UP, WIDTH
from snake.games.blocks.blocks_game import BlocksGame
from snake.games.blocks.const import TETROMINOES
from snake.types import Direction, Point


def _evaluate_placement(
    grid: dict[Point, Any],
    shape: str,
    target_x: int,
    target_y: int,
    rot: int,
) -> float:
    """Computes a heuristic score for a simulated piece placement on the cylinder."""
    simulated = set(grid.keys())
    for dx, dy in TETROMINOES[shape][rot]:
        simulated.add(Point((target_x + dx) % WIDTH, target_y + dy))

    # 1. Count cleared full rings around the cylinder
    lines_cleared = 0
    surviving_points = set()
    for y in range(HEIGHT):
        playable_xs = [x for x in range(WIDTH) if not led_map.is_impenetrable(x, y)]
        if playable_xs and all(Point(x, y) in simulated for x in playable_xs):
            lines_cleared += 1
        else:
            for x in playable_xs:
                if Point(x, y) in simulated:
                    surviving_points.add((x, y))

    # 2. Column heights across all columns of the cylinder
    col_heights: list[int] = []
    for x in range(WIDTH):
        floor_y = next((y - 1 for y in range(HEIGHT) if led_map.is_impenetrable(x, y)), HEIGHT - 1)
        highest_y = None
        for y in range(floor_y + 1):
            if (x, y) in surviving_points:
                highest_y = y
                break
        if highest_y is not None:
            col_heights.append(floor_y - highest_y + 1)
        else:
            col_heights.append(0)

    aggregate_height = sum(col_heights)

    # 3. Holes (empty cells below a block in the same column, above the floor)
    holes = 0
    for x in range(WIDTH):
        floor_y = next((y - 1 for y in range(HEIGHT) if led_map.is_impenetrable(x, y)), HEIGHT - 1)
        seen_block = False
        for y in range(floor_y + 1):
            if (x, y) in surviving_points:
                seen_block = True
            elif seen_block and not led_map.is_impenetrable(x, y):
                holes += 1

    # 4. Bumpiness (wrapping difference in height between adjacent columns on the cylinder)
    bumpiness = 0
    num_cols = len(col_heights)
    for i in range(num_cols):
        bumpiness += abs(col_heights[i] - col_heights[(i + 1) % num_cols])

    # Heuristic weights
    score = (
        (lines_cleared * 250.0)
        - (aggregate_height * 2.5)
        - (holes * 25.0)
        - (bumpiness * 1.5)
        + (target_y * 1.0)
    )
    return score


def blocks_agent_move(game: BlocksGame) -> Direction | None:
    """
    Determines the next move for the AI agent playing Blocks on the cylindrical screen.
    Searches possible rotations and column drops across all 14 columns, evaluates them using
    classic Tetris heuristics, and returns the next directional step via the shortest path.
    """
    if game.game_over or game.current_shape is None:
        return None

    shape = game.current_shape
    best_score = float("-inf")
    best_x = game.current_x
    best_rot = game.current_rotation

    # Evaluate all candidate rotations and column positions around the cylinder
    for rot in range(4):
        for x in range(WIDTH):
            if not game._is_valid_position(shape, x, 0, rot):
                continue

            # Drop piece to find landing y
            land_y = 0
            while game._is_valid_position(shape, x, land_y + 1, rot):
                land_y += 1

            score = _evaluate_placement(game.grid, shape, x, land_y, rot)
            if score > best_score:
                best_score = score
                best_x = x
                best_rot = rot

    # Navigate piece towards the best position
    if game.current_rotation != best_rot:
        return UP

    # Shortest circular distance around the cylinder
    diff = (best_x - game.current_x) % WIDTH
    if diff == 0:
        return DOWN
    elif diff <= WIDTH // 2:
        return RIGHT
    else:
        return LEFT
