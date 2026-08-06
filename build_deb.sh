#!/bin/bash
set -e

PKG_DIR="/tmp/llmchess_deb_pkg"
PROJ_DIR="/home/cat/Documents/trae_projects/trae/LLMChess"
VERSION="1.5.5"
DEB_FILE="$PROJ_DIR/llmchess_${VERSION}_all.deb"

echo "=== Building LLM Chess DEB package ==="

rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/usr/share/llmchess/chess_app"

cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: llmchess
Version: 1.5.0
Section: games
Priority: optional
Architecture: all
Depends: python3 (>= 3.9)
Recommends: python3-pyqt6, python3-chess, python3-httpx
Maintainer: LLMChess <llmchess@example.com>
Description: AI Chess - Play chess against local LLMs (AI vs AI supported)
 LLM Chess lets you play international chess against AI opponents
 powered by local large language models (LLMs), or watch two
 AIs play against each other.
 .
 Supports connecting to:
  - Ollama (http://localhost:11434)
  - llama.cpp server (http://localhost:8080)
  - LM Studio (http://localhost:1234)
  - Any OpenAI-compatible API endpoint
 .
 Features:
  - Interactive chess board with move highlighting
  - Pawn promotion dialog
  - Undo moves
  - Dark theme UI
  - FEN display and move history
  - AI vs AI mode with independent LLM configs per side
  - AI thinking/reasoning display panel
  - Multiple AI personas (aggressive/defensive/creative/teacher)
  - Adjustable AI vs AI speed with pause/step controls
 .
 Note: If Python dependencies are missing, the launcher will
 automatically attempt to install them via pip or apt.
EOF

cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/sh
set -e

if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

if [ -x /usr/bin/gtk-update-icon-cache ]; then
    /usr/bin/gtk-update-icon-cache /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

echo "LLM Chess installed! Run 'llmchess' from terminal or find it in your application menu."

exit 0
EOF

cat > "$PKG_DIR/usr/share/applications/llmchess.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=LLM Chess
Comment=Play chess against local AI models
Icon=llmchess
Exec=llmchess
Terminal=false
Categories=Game;BoardGame;
Keywords=chess;ai;llm;ollama;
StartupNotify=true
EOF

cat > "$PKG_DIR/usr/bin/llmchess" << 'EOF'
#!/bin/bash
APP_DIR="/usr/share/llmchess"

PYTHON=""
if [ -f "$HOME/miniconda3/bin/python3" ]; then
    PYTHON="$HOME/miniconda3/bin/python3"
elif [ -f "$HOME/anaconda3/bin/python3" ]; then
    PYTHON="$HOME/anaconda3/bin/python3"
elif [ -f "$HOME/mambaforge/bin/python3" ]; then
    PYTHON="$HOME/mambaforge/bin/python3"
elif [ -f "$HOME/micromamba/bin/python3" ]; then
    PYTHON="$HOME/micromamba/bin/python3"
else
    PYTHON="python3"
fi

check_modules() {
    "$PYTHON" -c "
import sys
try:
    import PyQt6
    import chess
    import httpx
    sys.exit(0)
except ImportError:
    sys.exit(1)
" 2>/dev/null
}

if ! check_modules; then
    echo "Missing Python dependencies detected!"
    echo "Attempting to install via pip..."

    if command -v pip3 >/dev/null 2>&1; then
        pip3 install PyQt6 python-chess httpx
    elif command -v pip >/dev/null 2>&1; then
        pip install PyQt6 python-chess httpx
    elif [ "$(id -u)" = "0" ] && command -v apt >/dev/null 2>&1; then
        apt update && apt install -y python3-pyqt6 python3-chess python3-httpx
    else
        if command -v zenity &>/dev/null; then
            zenity --error --title="LLM Chess" \
                --text="Missing Python dependencies.\n\nPlease install:\n  pip install PyQt6 python-chess httpx"
        fi
        echo "Error: Missing Python dependencies (PyQt6, python-chess, httpx)" >&2
        exit 1
    fi

    if ! check_modules; then
        if command -v zenity &>/dev/null; then
            zenity --error --title="LLM Chess" \
                --text="Failed to install Python dependencies.\n\nPlease install manually:\n  pip install PyQt6 python-chess httpx"
        fi
        echo "Error: Failed to install dependencies" >&2
        exit 1
    fi
fi

cd "$APP_DIR" && exec "$PYTHON" main.py "$@"
EOF

cp "$PROJ_DIR/main.py" "$PKG_DIR/usr/share/llmchess/"
cp "$PROJ_DIR/chess_app/__init__.py" "$PKG_DIR/usr/share/llmchess/chess_app/"
cp "$PROJ_DIR/chess_app/board_widget.py" "$PKG_DIR/usr/share/llmchess/chess_app/"
cp "$PROJ_DIR/chess_app/game_controller.py" "$PKG_DIR/usr/share/llmchess/chess_app/"
cp "$PROJ_DIR/chess_app/llm_connector.py" "$PKG_DIR/usr/share/llmchess/chess_app/"
cp "$PROJ_DIR/chess_app/settings_dialog.py" "$PKG_DIR/usr/share/llmchess/chess_app/"

echo "Generating icon..."
ICON_PATH="$PKG_DIR/usr/share/icons/hicolor/256x256/apps/llmchess.png"

/home/cat/miniconda3/bin/python3 -c "
from PyQt6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap, QPen
from PyQt6.QtCore import Qt, QRect

size = 256
pix = QPixmap(size, size)
pix.fill(QColor('#1E1E2E'))
painter = QPainter(pix)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
sq = size // 8
light = QColor('#F0D9B5')
dark = QColor('#B58863')
for r in range(8):
    for c in range(8):
        painter.fillRect(QRect(c*sq, r*sq, sq, sq), light if (r+c)%2==0 else dark)
font = QFont('Segoe UI Symbol', sq*3//4)
painter.setFont(font)
w = ['\u265C','\u265E','\u265D','\u265A','\u265B','\u265D','\u265E','\u265C']
b = ['\u2656','\u2658','\u2657','\u2654','\u2655','\u2657','\u2658','\u2656']
for c in range(8):
    painter.setPen(QColor('#FFFFFF'))
    painter.drawText(QRect(c*sq+1,7*sq+1,sq,sq),Qt.AlignmentFlag.AlignCenter,w[c])
    painter.setPen(QColor('#302E2B'))
    painter.drawText(QRect(c*sq,7*sq,sq,sq),Qt.AlignmentFlag.AlignCenter,w[c])
    painter.drawText(QRect(c*sq+1,6*sq+1,sq,sq),Qt.AlignmentFlag.AlignCenter,'\u265F')
    painter.setPen(QColor('#302E2B'))
    painter.drawText(QRect(c*sq,6*sq,sq,sq),Qt.AlignmentFlag.AlignCenter,'\u265F')
    painter.drawText(QRect(c*sq,0,sq,sq),Qt.AlignmentFlag.AlignCenter,b[c])
    painter.drawText(QRect(c*sq,sq,sq,sq),Qt.AlignmentFlag.AlignCenter,'\u2659')
painter.setPen(QPen(QColor('#585B70'),3))
painter.drawRect(1,1,size-2,size-2)
painter.end()
" 2>/dev/null

cp /tmp/llmchess.png "$ICON_PATH" 2>/dev/null || {
    /home/cat/miniconda3/bin/python3 -c "
from PyQt6.QtWidgets import QApplication
import sys
app = QApplication(sys.argv)
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap, QPen
from PyQt6.QtCore import Qt, QRect

size = 256
pix = QPixmap(size, size)
pix.fill(QColor('#1E1E2E'))
painter = QPainter(pix)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
sq = size // 8
light = QColor('#F0D9B5')
dark = QColor('#B58863')
for r in range(8):
    for c in range(8):
        painter.fillRect(QRect(c*sq, r*sq, sq, sq), light if (r+c)%2==0 else dark)
font = QFont('Segoe UI Symbol', sq*3//4)
painter.setFont(font)
w = ['\u265C','\u265E','\u265D','\u265A','\u265B','\u265D','\u265E','\u265C']
b = ['\u2656','\u2658','\u2657','\u2654','\u2655','\u2657','\u2658','\u2656']
for c in range(8):
    painter.setPen(QColor('#FFFFFF'))
    painter.drawText(QRect(c*sq+1,7*sq+1,sq,sq),Qt.AlignmentFlag.AlignCenter,w[c])
    painter.setPen(QColor('#302E2B'))
    painter.drawText(QRect(c*sq,7*sq,sq,sq),Qt.AlignmentFlag.AlignCenter,w[c])
    painter.drawText(QRect(c*sq+1,6*sq+1,sq,sq),Qt.AlignmentFlag.AlignCenter,'\u265F')
    painter.setPen(QColor('#302E2B'))
    painter.drawText(QRect(c*sq,6*sq,sq,sq),Qt.AlignmentFlag.AlignCenter,'\u265F')
    painter.drawText(QRect(c*sq,0,sq,sq),Qt.AlignmentFlag.AlignCenter,b[c])
    painter.drawText(QRect(c*sq,sq,sq,sq),Qt.AlignmentFlag.AlignCenter,'\u2659')
painter.setPen(QPen(QColor('#585B70'),3))
painter.drawRect(1,1,size-2,size-2)
painter.end()
pix.save('$ICON_PATH')
" 2>/dev/null
}
echo "Icon generated"

chmod 755 "$PKG_DIR/DEBIAN/postinst"
chmod 755 "$PKG_DIR/usr/bin/llmchess"

echo "Building .deb..."
dpkg-deb --build "$PKG_DIR" "$DEB_FILE"

echo ""
echo "=== Done! ==="
ls -lh "$DEB_FILE"
