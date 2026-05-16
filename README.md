# LLM Chess

Play international chess against AI opponents powered by local large language models (LLMs).

## Features

- **Interactive chess board** with move highlighting and last-move indicators
- **Pawn promotion** dialog
- **Undo moves** support
- **FEN display** and SAN move history
- **Dark theme** Catppuccin-style UI
- **Game status** detection (checkmate, stalemate, draw, etc.)

## Supported LLM Backends

Connects to any OpenAI-compatible API endpoint:

| Backend | Default URL | Notes |
|---------|-------------|-------|
| **Ollama** | `http://localhost:11434` | `ollama serve` |
| **llama.cpp Server** | `http://localhost:8080` | `./llama-server -m model.gguf --port 8080` |
| **LM Studio** | `http://localhost:1234` | Enable "Local Server" in Developer tab |
| **Custom** | Any URL | Configure in Settings |

## Installation

### From DEB package (Ubuntu/Debian)

```bash
sudo dpkg -i llmchess_1.0.0_all.deb
llmchess
```

### From source

```bash
# Install dependencies
pip install PyQt6 python-chess httpx

# Run
python3 main.py
```

### Build DEB package

```bash
bash build_deb.sh
sudo dpkg -i llmchess_1.0.0_all.deb
```

## Usage

1. **Start your LLM server** (Ollama, llama.cpp, or LM Studio)
2. **Launch LLM Chess** (`llmchess` or from application menu)
3. Click **Settings** to configure your LLM connection
4. Select **White** (you move first) or **Black** (AI moves first)
5. Click a piece, then click the destination square to move

### Settings

- **Provider**: Select your backend (Ollama, llama.cpp, LM Studio, or Custom)
- **Base URL**: API endpoint (auto-filled for presets)
- **Model**: Model name to use
- **Temperature**: Lower = more deterministic moves (default 0.3)
- **Max Tokens**: Maximum response length (default 512)
- **Test Connection**: Verify connectivity before playing

## Project Structure

```
LLMChess/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── build_deb.sh              # DEB package build script
├── chess_app/
│   ├── board_widget.py       # Chess board UI (PyQt6)
│   ├── llm_connector.py      # LLM API connector
│   ├── game_controller.py    # Main window & game controller
│   └── settings_dialog.py    # LLM connection settings
└── deb_pkg/                  # DEB packaging files
```

## How It Works

1. Each turn, the current board state is sent to the LLM as a **FEN string** plus a list of legal moves in **UCI format**
2. The LLM is prompted to respond with **only one UCI move** (e.g., `e2e4`, `g1f3`)
3. The response is parsed to extract the UCI move and validated against legal moves
4. If the LLM returns an invalid or empty response, the first legal move is used as fallback

## Requirements

- Python 3.9+
- PyQt6
- python-chess
- httpx
- A running LLM server (Ollama, llama.cpp, or LM Studio)

## License

MIT License
