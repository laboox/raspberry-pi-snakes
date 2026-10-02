from __future__ import annotations

import abc
from typing import Any

from snake.const import AGENT_GAME_SPEED, PLAYER_GAME_SPEED
from snake.types import Color, Point


class BaseGame(abc.ABC):
    """Abstract base class for all games playable on the LED matrix or screen."""

    @property
    def name(self) -> str:
        """Human-readable name of the game."""
        return self.__class__.__name__

    @property
    @abc.abstractmethod
    def game_over(self) -> bool:
        """Returns True if the current game session is over."""
        pass

    @abc.abstractmethod
    def initialize_game(self) -> None:
        """Initializes or resets the game state to start a new session."""
        pass

    @abc.abstractmethod
    def update_game(self) -> None:
        """Advances game state logic by one tick / frame."""
        pass

    @abc.abstractmethod
    def get_game_state(self) -> dict[Point, Color]:
        """
        Returns the current visual game state as a mapping from Point (x, y) to Color.
        The draw function in main uses this state to render to the display.
        """
        pass

    def handle_player_input(self, input_data: Any) -> None:
        """
        Handles player input (e.g., Direction, button press, key event).
        Can be overridden by interactive games.
        """
        pass

    @property
    def player_speed(self) -> float:
        """Player frame interval in seconds (lower is faster)."""
        return PLAYER_GAME_SPEED

    @property
    def agent_speed(self) -> float:
        """Agent frame interval in seconds (lower is faster)."""
        return AGENT_GAME_SPEED
