# Premium Snake Game

A feature-rich Snake game built with **Python**, **Pygame**, and **NumPy**. It includes multiple difficulty levels, customizable snake colors, visual effects, saved games, and a persistent high-score system.

## Features

- **Three difficulty levels:** Easy (slower, no obstacles), Medium (normal speed, some obstacles), and Hard (faster, more obstacles).
- **Customisation:** choose Green, Gold, or Purple for the snake.
- **Visual effects:** particle effects when food is collected.
- **Score tracking:** live score display and saved high scores.
- **Save and load:** save a game and continue it later.
- **Keyboard navigation:** use the menu and game controls without a mouse.

## Requirements

- Python 3.8 or newer
- Pygame
- NumPy

Install dependencies:

```bash
python -m pip install pygame numpy
```

## Run the game

```bash
git clone https://github.com/kiannaseri/snake-game-py.git
cd snake-game-py
python snake_game.py
```

On macOS/Linux, use `python3 snake_game.py` if `python` points to Python 2.

## Controls

| Action | Key |
|---|---|
| Move | Arrow keys or W / A / S / D |
| Pause / resume | Space |
| Save current game | P |
| Load saved game | L |
| Navigate menu options | 1–3 |
| Go back | Esc |

## Local game data

The game uses local files to keep player progress:

- `highscore.dat` — high-score data.
- `snake_save.json` — saved-game data.
- `savegame.json` and `replay.json` — additional game-state/replay data included in the repository.

Keep these files in the game directory when running the game.

## Troubleshooting

1. Confirm that Python is installed and available from your terminal.
2. Install or update the required packages: `python -m pip install --upgrade pygame numpy`.
3. If audio initialisation fails, check your audio device and Pygame installation; the game currently initialises Pygame's mixer at startup.

## Contributing

Bug reports and focused improvements are welcome. When submitting a change, describe what changed and include the steps used to test it.

## License

No license file is currently included. Check with the repository owner before redistributing or reusing this project.
