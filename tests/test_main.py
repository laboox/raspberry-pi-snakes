"""Tests for the main game module."""

from unittest.mock import patch

import pytest

from snake.main import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    get_next_head,
    initialize_game,
    is_safe,
    place_food,
)


class TestGameInitialization:
    """Test game initialization functions."""

    def test_initialize_game(self):
        """Test that game initialization sets up the game state correctly."""
        # Mock the global variables
        with (
            patch("snake.main.snake", []),
            patch("snake.main.food", ()),
            patch("snake.main.direction", RIGHT),
            patch("snake.main.score", 0),
            patch("snake.main.game_over", False),
            patch("snake.main.place_food") as mock_place_food,
        ):

            initialize_game()

            # Check that place_food was called
            mock_place_food.assert_called_once()

    def test_place_food_avoids_snake(self):
        """Test that food placement avoids snake positions."""
        # Mock the snake and MAP
        with (
            patch("snake.main.snake", [(5, 5), (5, 6), (6, 5)]),
            patch("snake.main.MAP", [[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
            patch("random.randint") as mock_randint,
        ):

            # Make random.randint return positions that are not on the snake
            mock_randint.side_effect = [1, 1]  # Position (1, 1) is not on snake

            place_food()

            # Verify that random.randint was called
            assert mock_randint.call_count >= 2


class TestGameLogic:
    """Test core game logic functions."""

    def test_get_next_head_basic(self):
        """Test basic head movement."""
        head = (5, 5)

        # Test movement in all directions
        assert get_next_head(head, UP) == (5, 4)
        assert get_next_head(head, DOWN) == (5, 6)
        assert get_next_head(head, LEFT) == (4, 5)
        assert get_next_head(head, RIGHT) == (6, 5)

    def test_get_next_head_wrapping(self):
        """Test that head movement wraps around the board edges."""
        with patch("snake.main.WIDTH", 10), patch("snake.main.HEIGHT", 10):

            # Test wrapping from left edge
            assert get_next_head((0, 5), LEFT) == (9, 5)

            # Test wrapping from right edge
            assert get_next_head((9, 5), RIGHT) == (0, 5)

    def test_is_safe_basic(self):
        """Test basic safety checking."""
        with (
            patch("snake.main.snake", [(5, 5), (5, 6), (6, 5)]),
            patch("snake.main.MAP", [[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        ):

            # Test safe positions
            assert is_safe(1, 1) is True
            assert is_safe(8, 8) is True

            # Test unsafe positions (on snake)
            assert is_safe(5, 5) is False
            assert is_safe(5, 6) is False
            assert is_safe(6, 5) is False

    def test_is_safe_wall_collision(self):
        """Test that walls are considered unsafe."""
        with (
            patch("snake.main.snake", []),
            patch("snake.main.MAP", [[0, -1, 0], [0, 0, 0], [0, 0, 0]]),
        ):

            # Position (1, 0) has a wall (-1)
            assert is_safe(1, 0) is False

            # Position (0, 0) is safe
            assert is_safe(0, 0) is True


class TestGameIntegration:
    """Test integration between game components."""

    @patch("snake.main.MAP", [[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    @patch("snake.main.WIDTH", 3)
    @patch("snake.main.HEIGHT", 3)
    def test_game_flow(self):
        """Test a basic game flow scenario."""
        # Initialize game
        with (
            patch("snake.main.snake", []),
            patch("snake.main.food", ()),
            patch("snake.main.direction", RIGHT),
            patch("snake.main.score", 0),
            patch("snake.main.game_over", False),
            patch("snake.main.place_food") as mock_place_food,
        ):

            initialize_game()
            mock_place_food.assert_called_once()

        # Test head movement
        head = (1, 1)
        new_head = get_next_head(head, RIGHT)
        assert new_head == (2, 1)

        # Test safety check
        with patch("snake.main.snake", [(1, 1), (0, 1)]):
            assert is_safe(2, 1) is True
            assert is_safe(1, 1) is False


if __name__ == "__main__":
    pytest.main([__file__])
