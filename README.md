# LLM Chess ️🤖

> Play chess against local LLMs, or watch two AIs battle each other — all in a beautiful dark-themed GUI.

[![PyPI version](https://badge.fury.io/py/llmchess.svg)](https://pypi.org/project/llmchess/)
[![npm version](https://badge.fury.io/js/llmchess.svg)](https://www.npmjs.com/package/llmchess)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/oemoem12/LLMChess)](https://github.com/oemoem12/LLMChess/releases)

LLM Chess is a desktop application that lets you play international chess against AI opponents powered by **local or cloud large language models**. Supports Ollama, llama.cpp, LM Studio, OpenAI GPT, DeepSeek, and any OpenAI-compatible API.

## ✨ Features

### 🎮 Game Modes
- **Human vs AI** — Classic mode. Play as White or Black against an LLM.
- **AI vs AI** — Watch two LLMs play each other with configurable speed control (pause/resume/step).
- Each side can use a **different model, different backend, different temperature**.

### 💭 AI Thinking Display
- See the AI's **reasoning process** for every move
- Color-coded by side (blue for White, pink for Black)
- Parses `Reasoning:` and `Move:` format with fallback handling

### 🎭 AI Personas
Choose the AI's "personality" — affects its playing style and reasoning tone:
- **Default** — Calm, professional engine
- **Aggressive** — Loves attacks and sacrifices
- **Defensive** — Values king safety and solid positions
- **Creative** — Unusual openings and tactical surprises
- **Teacher** — Explains reasoning clearly, great for learning

### 🎨 UI Highlights
- Dark Catppuccin-themed PyQt6 interface
- Click-to-move with legal-move highlighting
- Last-move markers (yellow) and check indicators (red)
- Full move history in SAN notation
- Real-time FEN display
- Promotion dialog (queen/rook/bishop/knight)
- Undo moves

## 📦 Installation

### Option 1: pip (recommended)
```bash
pip install llmchess
llmchess
```

Or run as a module:
```bash
python -m llmchess
```

### Option 2: npm (Node.js)
```bash
npm install -g llmchess
llmchess
```
The npm wrapper will auto-install the Python `llmchess` package on first run.

### Option 3: DEB package (Ubuntu/Debian)
```bash
sudo dpkg -i llmchess_1.5.5_all.deb
```
The launcher will auto-install missing Python dependencies (PyQt6, python-chess, httpx).

### Option 4: From source
```bash
git clone https://github.com/oemoem12/LLMChess.git
cd LLMChess
pip install -e .
python main.py
```

## 🔧 Setup LLM Backend

LLM Chess is **backend-agnostic** — it speaks OpenAI-compatible HTTP API. Pick any one:

### Ollama (easiest)
```bash
# Install from https://ollama.com
ollama pull qwen2.5:7b
ollama serve  # default: http://localhost:11434
```

### llama.cpp
```bash
./llama-server -m model.gguf --port 8080
```

### LM Studio
Open LM Studio → Developer tab → Start Local Server (default: `http://localhost:1234`)

## 🚀 Quick Start

1. **Start your LLM server** (Ollama/llama.cpp/LM Studio)
2. **Launch LLM Chess**: `llmchess`
3. **Open Settings** → select your backend → click **Test Connection**
4. **Choose a model** in the connection settings
5. **Pick a game mode** (Human vs AI / AI vs AI) and a persona
6. **Click a piece → click target square** to move
7. **Watch the AI Thinking panel** to see your opponent's reasoning

## 🎬 Screenshots

```
┌─────────────────────┬──────────────────┐
│  Game Mode          │  Move History    │
│  [Human vs AI ▼]    │  1. e4 e5        │
│  [White (first) ▼]  │  2. Nf3 Nc6      │
│                     │  3. Bb5 a6       │
│  ♔ ♕ ♖ ♗ ♘ ♙        │  ...             │
│  ─────────────────  │                  │
│  Chess Board        │  AI Thinking     │
│  (8×8)              │  ━━━ White AI ━━ │
│  ─────────────────  │  Move: e2e4      │
│  [New Game] [⚙ Set] │  Reasoning:      │
│                     │  Classical king  │
└─────────────────────┴──────────────────┘
```

## 🛠️ Tech Stack

- **[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)** — Cross-platform GUI
- **[python-chess](https://python-chess.readthedocs.io/)** — Chess rules, FEN/PGN handling
- **[httpx](https://www.python-httpx.org/)** — OpenAI-compatible HTTP client
- **[setuptools](https://setuptools.pypa.io/)** + **Trusted Publisher** — Zero-token PyPI release

## 📐 Architecture

```
chess_app/
├── __init__.py            # Package entry, version, main()
├── __main__.py            # python -m chess_app support
├── main.py                # GUI entry point
├── board_widget.py        # Chess board renderer (PyQt6)
├── game_controller.py     # Main window + game flow + AI vs AI logic
├── llm_connector.py       # OpenAI-compatible LLM client + persona prompts
└── settings_dialog.py     # Tabbed config UI (White/Black sides)
```

## 🤝 Contributing

PRs welcome! Some ideas:
- [ ] Save/load PGN files
- [ ] Tournament mode (round-robin between N models)
- [ ] Stockfish-LLM hybrid (use Stockfish for blunders, LLM for variety)
- [ ] Post-game analysis with LLM commentary
- [ ] Online multiplayer via WebSocket

## 📜 License

[MIT](LICENSE) — do whatever you want, just don't blame me if the AI hangs your king.

## 🔗 Links

- **PyPI**: https://pypi.org/project/llmchess/
- **GitHub**: https://github.com/oemoem12/LLMChess
- **Issues**: https://github.com/oemoem12/LLMChess/issues
- **中文 README**: [README_zh.md](README_zh.md)
