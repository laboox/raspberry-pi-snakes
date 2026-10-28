from __future__ import annotations

from snake.const import HEIGHT, WIDTH
from snake.games.base_game import BaseGame
from snake.games.text.const import (
    CHAR_SPACING,
    CHAR_WIDTH,
    DEFAULT_TEXT,
    DEFAULT_TEXT_COLOR,
    FONT_3X5,
    TEXT_AGENT_SPEED,
    TEXT_PLAYER_SPEED,
    TEXT_START_Y,
)
from snake.types import Color, Point


class TextGame(BaseGame):
    """
    Scrolling text display game for the cylindrical LED screen.
    Uses a 3x5 pixel bitmap font on rows 3..7. The first character
    starts at the far right edge of the screen (x = WIDTH - 1) and scrolls left
    until the last character finishes scrolling off the left edge (x < 0).
    """

    def __init__(
        self,
        text: str = DEFAULT_TEXT,
        color: Color = DEFAULT_TEXT_COLOR,
    ) -> None:
        self.text: str = text
        self.color: Color = color
        self.current_x: int = WIDTH - 1
        self._game_over: bool = False

    @property
    def name(self) -> str:
        return "Text"

    @property
    def game_over(self) -> bool:
        return self._game_over

    @game_over.setter
    def game_over(self, value: bool) -> None:
        self._game_over = value

    @property
    def player_speed(self) -> float:
        return TEXT_PLAYER_SPEED

    @property
    def agent_speed(self) -> float:
        return TEXT_AGENT_SPEED

    @property
    def text_width(self) -> int:
        """Total horizontal width in pixels of the rendered text string."""
        if not self.text:
            return 0
        num_chars = len(self.text)
        return num_chars * CHAR_WIDTH + (num_chars - 1) * CHAR_SPACING

    def set_text(self, text: str) -> None:
        """Sets a new text string and resets the scrolling session."""
        self.text = text
        self.initialize_game()

    def initialize_game(self) -> None:
        """Initializes text with the first character at the far right edge."""
        self.current_x = WIDTH - 1
        self._game_over = len(self.text) == 0

    def update_game(self) -> None:
        """Advances text one column left until the last character exits."""
        if self._game_over:
            return

        self.current_x -= 1
        if self.current_x + self.text_width <= 0:
            self._game_over = True

    def get_game_state(self) -> dict[Point, Color]:
        """Returns visible text pixels as a mapping from Point to Color."""
        state: dict[Point, Color] = {}
        if self._game_over or not self.text:
            return state

        step = CHAR_WIDTH + CHAR_SPACING
        for idx, ch in enumerate(self.text.upper()):
            glyph = FONT_3X5.get(ch, FONT_3X5["?"])
            char_x = self.current_x + idx * step
            for row_idx, row in enumerate(glyph):
                py = TEXT_START_Y + row_idx
                if py < 0 or py >= HEIGHT:
                    continue
                for col_idx, pixel in enumerate(row):
                    if pixel == "#":
                        px = char_x + col_idx
                        if 0 <= px < WIDTH:
                            state[Point(px, py)] = self.color

        return state
