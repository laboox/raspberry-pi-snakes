---
name: project-style
description: >-
  Enforces coding style, packaging, naming, and dependency conventions for the
  raspberry-pi-snakes project. Activate this skill whenever creating, modifying,
  refactoring, or testing Python files or games in this repository.
---

# Project Style & Conventions (`raspberry-pi-snakes`)

Follow these rules strictly whenever writing or modifying code in this repository.

## 1. No `__init__.py` Files
- **Do not create `__init__.py` files** in new packages or subdirectories (such as `snake/games/<new_game>/`).
- Python 3 implicit namespace packages are used; `__init__.py` files are unnecessary and should be omitted.

## 2. No Extra Naming or Aliases
- **Use a single canonical name** for every type, class, enum, function, and constant.
- **Do not create aliases** (e.g., `ColorEffect = Effect`), re-exports, or duplicate wrapper methods/parameters for convenience or backward compatibility.
- Import and reference symbols by their canonical definition directly (e.g., `Effect`, `Point`, `Color`, `Direction` from `snake.types`).

## 3. `pygame` Is Required — No Workarounds
- **`pygame` must be imported and used directly** (`import pygame` at module top level).
- **Never include workarounds for missing `pygame`**:
  - Do not wrap `import pygame` in `try ... except ImportError`.
  - Do not create dummy/mock/stub `pygame` classes or fallback modes when `pygame` is not found.
  - Only hardware-specific Raspberry Pi libraries (`board`, `neopixel_spi`) may fall back to desktop `pygame` rendering in `Renderer._init_display()`.
- Always execute tests and scripts using the project's virtual environment (e.g., `.venv/bin/pytest` or `uv run pytest`) where `pygame` is installed and working.

## 4. Code Style, Typing & Structure
- **Type Annotations**: Start files with `from __future__ import annotations` and include complete type annotations on all function signatures (`mypy` is configured with `disallow_untyped_defs = true`).
- **Formatting & Linting**:
  - `black` with `line-length = 100`
  - `isort` with `profile = "black"`
  - `flake8` with `max-line-length = 100`
- **File Organization**:
  - Games live under `snake/games/<game_name>/` and subclass `BaseGame` (`snake/games/base_game.py`).
  - Co-locate unit tests alongside source files using the `*_test.py` naming convention (e.g., `snake/games/blocks/blocks_game_test.py`, `snake/renderer_test.py`).
