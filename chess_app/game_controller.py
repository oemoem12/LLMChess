import chess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QGroupBox, QComboBox, QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QTextCursor

from chess_app.board_widget import ChessBoardWidget
from chess_app.llm_connector import LLMConnector, LLMConfig
from chess_app.settings_dialog import SettingsDialog


class LLMWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, connector: LLMConnector, fen: str, legal_moves: list[str]):
        super().__init__()
        self.connector = connector
        self.fen = fen
        self.legal_moves = legal_moves

    def run(self):
        try:
            move = self.connector.get_move(self.fen, self.legal_moves)
            self.finished.emit(move)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LLM Chess - AI Opponent")
        self.setMinimumSize(700, 560)

        self._config = LLMConfig()
        self._connector = LLMConnector(self._config)
        self._worker_thread: QThread | None = None
        self._worker: LLMWorker | None = None
        self._move_history: list[str] = []

        self._init_ui()
        self._start_new_game()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(6)

        color_group = QGroupBox("Play As")
        color_layout = QHBoxLayout(color_group)
        self.color_combo = QComboBox()
        self.color_combo.addItem("White (You go first)")
        self.color_combo.addItem("Black (AI goes first)")
        self.color_combo.currentIndexChanged.connect(self._on_color_changed)
        color_layout.addWidget(self.color_combo)
        left_panel.addWidget(color_group)

        self.board_widget = ChessBoardWidget()
        self.board_widget.setMinimumSize(480, 480)
        self.board_widget.move_made.connect(self._on_user_move)
        left_panel.addWidget(self.board_widget, 1)

        button_layout = QHBoxLayout()

        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.clicked.connect(self._start_new_game)
        button_layout.addWidget(self.new_game_btn)

        self.settings_btn = QPushButton("Settings...")
        self.settings_btn.clicked.connect(self._open_settings)
        button_layout.addWidget(self.settings_btn)

        left_panel.addLayout(button_layout)

        main_layout.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(6)

        move_group = QGroupBox("Move History")
        move_layout = QVBoxLayout(move_group)
        self.move_history_text = QTextEdit()
        self.move_history_text.setReadOnly(True)
        self.move_history_text.setFont(QFont("Consolas", 11))
        self.move_history_text.setMinimumWidth(200)
        move_layout.addWidget(self.move_history_text)
        right_panel.addWidget(move_group, 1)

        info_group = QGroupBox("Game Status")
        info_layout = QVBoxLayout(info_group)
        self.status_label = QLabel("Ready. Make your move.")
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont("Segoe UI", 10))
        info_layout.addWidget(self.status_label)

        self.fen_label = QLabel()
        self.fen_label.setWordWrap(True)
        self.fen_label.setFont(QFont("Consolas", 8))
        self.fen_label.setStyleSheet("color: #888;")
        info_layout.addWidget(self.fen_label)

        self.thinking_label = QLabel("")
        self.thinking_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        info_layout.addWidget(self.thinking_label)

        self.undo_btn = QPushButton("Undo Last Move")
        self.undo_btn.clicked.connect(self._undo_move)
        info_layout.addWidget(self.undo_btn)

        right_panel.addWidget(info_group)

        main_layout.addLayout(right_panel)

    def _start_new_game(self):
        self._cleanup_worker()

        self._move_history = []
        self.move_history_text.clear()
        self.thinking_label.setText("")

        player_color = chess.WHITE if self.color_combo.currentIndex() == 0 else chess.BLACK
        self.board_widget.set_player_color(player_color)
        self.board_widget.set_position(chess.STARTING_FEN)

        self._update_status()

        if player_color == chess.BLACK:
            self._request_llm_move()

    def _on_color_changed(self):
        self._start_new_game()

    def _on_user_move(self, uci_move: str):
        self._move_history.append(uci_move)
        self._update_history_display()
        self._update_status()

        board = self.board_widget.board

        if board.is_game_over():
            self._update_status()
            return

        if board.turn != self.board_widget._player_color:
            self._request_llm_move()

    def _request_llm_move(self):
        board = self.board_widget.board

        if board.is_game_over():
            return

        legal_moves = self.board_widget.get_legal_moves_uci()
        if not legal_moves:
            return

        self.thinking_label.setText("AI is thinking...")
        self.status_label.setText("Waiting for AI...")
        self.board_widget.setEnabled(False)
        self.new_game_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.undo_btn.setEnabled(False)
        self.color_combo.setEnabled(False)

        QApplication.processEvents()

        self._worker_thread = QThread()
        self._worker = LLMWorker(self._connector, board.fen(), legal_moves)
        self._worker.moveToThread(self._worker_thread)

        self._worker.finished.connect(self._on_llm_move)
        self._worker.error.connect(self._on_llm_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)

        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    def _on_llm_move(self, move_uci: str):
        self._restore_ui()
        self._cleanup_worker()

        if move_uci:
            self._move_history.append(move_uci)
            self.board_widget.LLM_play_move(move_uci)
            self._update_history_display()
            self._update_status()

    def _on_llm_error(self, error_msg: str):
        self._restore_ui()
        self._cleanup_worker()

        QMessageBox.warning(
            self, "AI Error",
            f"Failed to get move from LLM:\n\n{error_msg}\n\n"
            "Please check your LLM connection settings and ensure the server is running."
        )
        self.status_label.setText(f"Error: {error_msg[:100]}")

    def _restore_ui(self):
        self.board_widget.setEnabled(True)
        self.new_game_btn.setEnabled(True)
        self.settings_btn.setEnabled(True)
        self.undo_btn.setEnabled(True)
        self.color_combo.setEnabled(True)
        self.thinking_label.setText("")

    def _cleanup_worker(self):
        if self._worker_thread is not None:
            try:
                self._worker_thread.quit()
                self._worker_thread.wait(3000)
            except RuntimeError:
                pass
        self._worker_thread = None
        self._worker = None

    def _update_status(self):
        board = self.board_widget.board
        self.fen_label.setText(f"FEN: {board.fen()}")

        if board.is_game_over():
            result = board.result()
            if result == "1-0":
                msg = "Game Over - White Wins!"
            elif result == "0-1":
                msg = "Game Over - Black Wins!"
            elif result == "1/2-1/2":
                msg = "Game Over - It's a Draw!"
            else:
                msg = f"Game Over - {result}"

            if board.is_checkmate():
                msg += " (Checkmate)"
            elif board.is_stalemate():
                msg += " (Stalemate)"
            elif board.is_insufficient_material():
                msg += " (Insufficient Material)"
            elif board.is_fifty_moves():
                msg += " (50-Move Rule)"
            elif board.is_repetition():
                msg += " (Threefold Repetition)"

            self.status_label.setText(msg)
            self.thinking_label.setText("")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        elif board.is_check():
            self.status_label.setText(f"{'White' if board.turn == chess.WHITE else 'Black'} is in check!")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            turn = "Your" if board.turn == self.board_widget._player_color else "AI's"
            color_name = "White" if board.turn == chess.WHITE else "Black"
            self.status_label.setText(f"{color_name}'s turn ({turn} turn)")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: normal;")

    def _update_history_display(self):
        board = chess.Board()
        lines = []
        move_num = 1

        for i, uci in enumerate(self._move_history):
            try:
                move = chess.Move.from_uci(uci)
                if move in board.legal_moves:
                    if board.turn == chess.WHITE:
                        lines.append(f"{move_num}. {board.san(move)}")
                    else:
                        lines[-1] += f"  {board.san(move)}"
                        move_num += 1
                    board.push(move)
                else:
                    if board.turn == chess.WHITE:
                        lines.append(f"{move_num}. {uci}")
                    else:
                        if lines:
                            lines[-1] += f"  {uci}"
                        else:
                            lines.append(f"{move_num}. ... {uci}")
                        move_num += 1
            except ValueError:
                if board.turn == chess.WHITE:
                    lines.append(f"{move_num}. {uci}")
                else:
                    if lines:
                        lines[-1] += f"  {uci}"
                    else:
                        lines.append(f"{move_num}. ... {uci}")
                    move_num += 1

        self.move_history_text.setPlainText("\n".join(lines))
        cursor = self.move_history_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.move_history_text.setTextCursor(cursor)

    def _undo_move(self):
        board = self.board_widget.board
        if board.move_stack:
            if len(board.move_stack) >= 2:
                board.pop()
                board.pop()
                self._move_history = self._move_history[:-2]
            else:
                board.pop()
                self._move_history = self._move_history[:-1]

            self.board_widget.set_position(board.fen())
            self.board_widget._human_turn = (
                board.turn == self.board_widget._player_color
            )
            self.board_widget.update()
            self._update_history_display()
            self._update_status()

    def _open_settings(self):
        dlg = SettingsDialog(self._config, self)
        dlg.set_test_callback(lambda: self._test_connection(dlg))
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            self._config = dlg.get_config()
            self._connector = LLMConnector(self._config)
            self._start_new_game()

    def _test_connection(self, dlg: SettingsDialog):
        config = dlg.get_config()
        connector = LLMConnector(config)
        try:
            success, message = connector.test_connection()
            dlg.set_test_status(success, message)
        except Exception as e:
            dlg.set_test_status(False, str(e))
        finally:
            connector.close()

    def closeEvent(self, event):
        self._cleanup_worker()
        self._connector.close()
        super().closeEvent(event)