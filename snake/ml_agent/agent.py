import pathlib
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from snake import led_map_v2 as led_map
from snake import snake_game
from snake.const import DIRECTIONS
from snake.types import Direction

WIDTH = len(led_map.MAP[0])  # 14
HEIGHT = len(led_map.MAP)  # 8


def get_state(game: snake_game.SnakeGame):
    state = np.zeros((WIDTH, HEIGHT, 2))
    snake_len = len(game.snake)
    for i, snake_part in enumerate(game.snake):
        state[snake_part.x, snake_part.y, 0] = ((snake_len - i) / snake_len / 2) + 0.5
    state[game.food.x, game.food.y, 1] = 1
    return state.flatten()


class DQN(nn.Module):

    def __init__(self, n_observations, n_actions):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, n_observations * 2)
        self.layer2 = nn.Linear(n_observations * 2, n_observations)
        self.layer3 = nn.Linear(n_observations, n_actions * 2)
        self.layer4 = nn.Linear(n_actions * 2, n_actions)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, x):
        x = F.leaky_relu(self.layer1(x))
        x = F.leaky_relu(self.layer2(x))
        x = F.leaky_relu(self.layer3(x))
        return self.layer4(x)


# Global model instance
_model: Optional[DQN] = None
_device = torch.device(
    "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
)


def _load_model() -> DQN:
    """Load the trained model from checkpoint file."""
    global _model

    if _model is not None:
        return _model

    # Calculate model dimensions
    n_actions = 4  # UP, DOWN, LEFT, RIGHT
    n_observations = WIDTH * HEIGHT * 2  # 14 * 8 * 2 = 224

    # Initialize model
    model = DQN(n_observations, n_actions).to(_device)

    # Try to find checkpoint file in multiple locations
    policy_number = 1600
    possible_paths = [
        pathlib.Path(__file__).parent / f"policy_{policy_number}.checkpoint",
        pathlib.Path(__file__).parent.parent.parent / f"policy_{policy_number}.checkpoint",
    ]

    checkpoint_path = None
    for path in possible_paths:
        if path.exists():
            checkpoint_path = path
            break

    if checkpoint_path is None:
        # If no checkpoint found, return untrained model
        print("Warning: No checkpoint file found. Using untrained model.")
        print(f"Looked for checkpoint in: {[str(p) for p in possible_paths]}")
        _model = model
        return _model

    try:
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=_device)
        model.load_state_dict(checkpoint)
        model.eval()  # Set to evaluation mode
        print(f"Loaded model from {checkpoint_path}")
    except Exception as e:
        print(f"Error loading checkpoint from {checkpoint_path}: {e}")
        print("Using untrained model.")

    _model = model
    return _model


def agent_move(game: snake_game.SnakeGame) -> Optional[Direction]:
    """
    Determines the next move for the ML agent using the trained DQN model.

    Args:
        game: The current SnakeGame instance

    Returns:
        The best direction to move, or None if no valid move is found
    """
    model = _load_model()

    # Get current state
    state = get_state(game)
    state_tensor = torch.tensor(state, dtype=torch.float32, device=_device).unsqueeze(0)

    # Get Q-values from model
    with torch.no_grad():
        q_values = model(state_tensor)

    # Get action indices sorted by Q-value (highest first)
    action_scores = q_values[0].cpu().numpy()
    sorted_actions = np.argsort(action_scores)[::-1]  # Descending order
    print(f"Action scores: {action_scores}")
    print(f"Sorted actions: {sorted_actions}")

    # Try actions in order of Q-value, but only if they're safe
    head = game.snake_head

    for action_idx in sorted_actions:
        direction = DIRECTIONS[action_idx]
        next_head = snake_game.get_next_head(head, direction)

        # Check if this move is safe
        if game.is_safe(next_head):
            return direction

    # No safe move found
    return None
