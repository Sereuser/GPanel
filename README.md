# GPanel

**GPanel** is a powerful game server monitor and auto-restart tool, made by Vaka.

## Features

- Real-time server status monitoring
- Automatic server restart on failure
- Customizable configuration via `config.json`
- Minimal and clean UI based on PyQt6
- Works with SRCDS (Source Dedicated Server)
- Debug mode with debug output (`--test` flag)

## License

This project is licensed under the [MIT License](LICENSE).

## Usage

1. Edit `config.json` with your server details.
2. Run the app:
   - Normal mode (no debug):  
     ```bash
     python main.py
     ```
   - Debug mode (with debug):  
     ```bash
     python main.py --test
     ```
3. To build executable (Windows recommended):  
   ```bash
   pyinstaller --onefile --noconsole main.py
