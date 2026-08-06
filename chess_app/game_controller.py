"""
Game Controller - 主窗口和游戏逻辑
支持人机对弈和 AI 对弈模式，集成 i18n 双语支持
"""

import chess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QGroupBox, QComboBox, QMessageBox,
    QApplication, QCheckBox, QSlider, QFormLayout,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QTextCursor, QColor

from chess_app.board_widget import ChessBoardWidget
from chess_app.llm_connector import LLMConnector, LLMConfig, LLMResponse
from chess_app.settings_dialog import SettingsDialog
from chess_app.i18n import tr, set_language, get_language


# ============================================================================
# Worker：在独立线程中调用 LLM
# ============================================================================

class LLMWorker(QObject):
    """单次 LLM 调用的 worker"""
    finished = pyqtSignal(object)  # 发出 LLMResponse
    error = pyqtSignal(str)

    def __init__(self, connector: LLMConnector, fen: str, legal_moves: list[str], side: str = ""):
        super().__init__()
        self.connector = connector
        self.fen = fen
        self.legal_moves = legal_moves
        self.side = side

    def run(self):
        try:
            response = self.connector.get_move(self.fen, self.legal_moves, self.side)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


# ============================================================================
# 主窗口
# ============================================================================

# 游戏模式常量
MODE_HUMAN_VS_AI = "human_vs_ai"   # 人 vs AI
MODE_AI_VS_AI = "ai_vs_ai"         # AI vs AI


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(900, 640)

        # 状态
        self._config_white = LLMConfig()  # 白方配置
        self._config_black = LLMConfig()  # 黑方配置
        self._config = self._config_white  # 当前主配置（向后兼容）
        self._connector_white = LLMConnector(self._config_white)
        self._connector_black = LLMConnector(self._config_black)

        self._worker_thread: QThread | None = None
        self._worker: LLMWorker | None = None
        self._move_history: list[dict] = []

        # 模式
        self._mode = MODE_HUMAN_VS_AI

        self._init_ui()
        self._start_new_game()

    # ------------------------------------------------------------------
    # UI 初始化
    # ------------------------------------------------------------------

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ===== 左面板 =====
        left_panel = QVBoxLayout()
        left_panel.setSpacing(6)

        # 模式选择
        mode_group = QGroupBox(tr("mode_group"))
        mode_layout = QVBoxLayout(mode_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(tr("mode_human_vs_ai"), MODE_HUMAN_VS_AI)
        self.mode_combo.addItem(tr("mode_ai_vs_ai"), MODE_AI_VS_AI)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        # 人类执方（仅在 Human vs AI 时可见）
        self.color_combo = QComboBox()
        self.color_combo.addItem(tr("color_white_first"))
        self.color_combo.addItem(tr("color_black_first"))
        self.color_combo.currentIndexChanged.connect(self._on_color_changed)
        mode_layout.addWidget(self.color_combo)

        left_panel.addWidget(mode_group)

        # 棋盘
        self.board_widget = ChessBoardWidget()
        self.board_widget.setMinimumSize(480, 480)
        self.board_widget.move_made.connect(self._on_user_move)
        left_panel.addWidget(self.board_widget, 1)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.new_game_btn = QPushButton(tr("btn_new_game"))
        self.new_game_btn.clicked.connect(self._start_new_game)
        button_layout.addWidget(self.new_game_btn)

        self.settings_btn = QPushButton(tr("btn_settings"))
        self.settings_btn.clicked.connect(self._open_settings)
        button_layout.addWidget(self.settings_btn)

        # AI vs AI 控制
        self.pause_btn = QPushButton(tr("btn_pause"))
        self.pause_btn.clicked.connect(self._toggle_ai_vs_ai_pause)
        self.pause_btn.setVisible(False)
        button_layout.addWidget(self.pause_btn)

        self.step_btn = QPushButton(tr("btn_step"))
        self.step_btn.clicked.connect(self._ai_vs_ai_step)
        self.step_btn.setVisible(False)
        button_layout.addWidget(self.step_btn)

        left_panel.addLayout(button_layout)

        # AI vs AI 速度控制
        self.speed_group = QGroupBox(tr("group_ai_vs_ai_speed"))
        speed_layout = QHBoxLayout(self.speed_group)
        speed_layout.addWidget(QLabel(tr("label_delay")))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(0)
        self.speed_slider.setMaximum(5000)
        self.speed_slider.setValue(1000)
        self.speed_slider.setTickInterval(500)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        speed_layout.addWidget(self.speed_slider)
        self.speed_label = QLabel("1.0s")
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v/1000:.1f}s")
        )
        speed_layout.addWidget(self.speed_label)
        self.speed_group.setVisible(False)
        left_panel.addWidget(self.speed_group)

        main_layout.addLayout(left_panel, 1)

        # ===== 右面板 =====
        right_panel = QVBoxLayout()
        right_panel.setSpacing(6)

        # 走棋历史
        move_group = QGroupBox(tr("group_move_history"))
        move_layout = QVBoxLayout(move_group)
        self.move_history_text = QTextEdit()
        self.move_history_text.setReadOnly(True)
        self.move_history_text.setFont(QFont("Consolas", 11))
        self.move_history_text.setMinimumWidth(220)
        move_layout.addWidget(self.move_history_text)
        right_panel.addWidget(move_group, 1)

        # AI 思考显示
        self.thinking_group = QGroupBox(tr("group_ai_thinking"))
        thinking_layout = QVBoxLayout(self.thinking_group)
        self.thinking_text = QTextEdit()
        self.thinking_text.setReadOnly(True)
        self.thinking_text.setFont(QFont("Segoe UI", 10))
        self.thinking_text.setMinimumHeight(120)
        self.thinking_text.setStyleSheet(
            "background-color: #2A2A3C; color: #E0E0E0; "
            "border: 1px solid #585B70; border-radius: 4px; padding: 6px;"
        )
        thinking_layout.addWidget(self.thinking_text)
        right_panel.addWidget(self.thinking_group, 1)

        # 游戏状态
        info_group = QGroupBox(tr("group_game_status"))
        info_layout = QVBoxLayout(info_group)
        self.status_label = QLabel(tr("status_ready"))
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont("Segoe UI", 10))
        info_layout.addWidget(self.status_label)

        self.fen_label = QLabel()
        self.fen_label.setWordWrap(True)
        self.fen_label.setFont(QFont("Consolas", 8))
        self.fen_label.setStyleSheet("color: #888;")
        info_layout.addWidget(self.fen_label)

        self.undo_btn = QPushButton(tr("btn_undo"))
        self.undo_btn.clicked.connect(self._undo_move)
        info_layout.addWidget(self.undo_btn)

        right_panel.addWidget(info_group)

        main_layout.addLayout(right_panel)

    # ------------------------------------------------------------------
    # 语言切换
    # ------------------------------------------------------------------

    def _update_ui_language(self):
        """更新所有 UI 文本为当前语言"""
        self.setWindowTitle(tr("app_title"))
        self.new_game_btn.setText(tr("btn_new_game"))
        self.settings_btn.setText(tr("btn_settings"))
        self.pause_btn.setText(tr("btn_pause") if not self._ai_vs_ai_paused else tr("btn_resume"))
        self.step_btn.setText(tr("btn_step"))
        self.undo_btn.setText(tr("btn_undo"))

        # 更新 GroupBox 标题
        for group in self.findChildren(QGroupBox):
            title = group.title()
            if "Game Mode" in title or "游戏模式" in title:
                group.setTitle(tr("mode_group"))
            elif "Move History" in title or "走棋历史" in title:
                group.setTitle(tr("group_move_history"))
            elif "AI Thinking" in title or "AI 思考" in title:
                group.setTitle(tr("group_ai_thinking"))
            elif "Game Status" in title or "游戏状态" in title:
                group.setTitle(tr("group_game_status"))
            elif "Speed" in title or "速度" in title:
                group.setTitle(tr("group_ai_vs_ai_speed"))

        # 更新下拉框
        self.mode_combo.setItemText(0, tr("mode_human_vs_ai"))
        self.mode_combo.setItemText(1, tr("mode_ai_vs_ai"))
        self.color_combo.setItemText(0, tr("color_white_first"))
        self.color_combo.setItemText(1, tr("color_black_first"))

        self._update_status()

    # ------------------------------------------------------------------
    # 模式切换
    # ------------------------------------------------------------------

    def _on_mode_changed(self):
        new_mode = self.mode_combo.currentData()
        self._mode = new_mode

        if new_mode == MODE_AI_VS_AI:
            self.color_combo.setVisible(False)
            self.undo_btn.setVisible(False)
            self.pause_btn.setVisible(True)
            self.step_btn.setVisible(True)
            self.speed_group.setVisible(True)
            self.board_widget.set_player_color(None)
        else:
            self.color_combo.setVisible(True)
            self.undo_btn.setVisible(True)
            self.pause_btn.setVisible(False)
            self.step_btn.setVisible(False)
            self.speed_group.setVisible(False)
            player_color = chess.WHITE if self.color_combo.currentIndex() == 0 else chess.BLACK
            self.board_widget.set_player_color(player_color)

        self._start_new_game()

    # ------------------------------------------------------------------
    # 游戏流程
    # ------------------------------------------------------------------

    def _start_new_game(self):
        self._cleanup_worker()
        self._ai_vs_ai_paused = False
        self._ai_vs_ai_active = False

        self._move_history = []
        self.move_history_text.clear()
        self.thinking_text.clear()

        self.board_widget.set_position(chess.STARTING_FEN)

        if self._mode == MODE_HUMAN_VS_AI:
            player_color = chess.WHITE if self.color_combo.currentIndex() == 0 else chess.BLACK
            self.board_widget.set_player_color(player_color)

        self._update_status()

        # 启动 AI 走棋
        if self._mode == MODE_AI_VS_AI:
            self._ai_vs_ai_active = True
            self.pause_btn.setText(tr("btn_pause"))
            QTimer.singleShot(500, self._ai_vs_ai_step)
        else:
            player_color = self.board_widget._player_color
            if player_color == chess.BLACK:
                self._request_llm_move(chess.WHITE)

    def _on_color_changed(self):
        if self._mode == MODE_HUMAN_VS_AI:
            self._start_new_game()

    def _on_user_move(self, uci_move: str):
        if self._mode != MODE_HUMAN_VS_AI:
            return

        self.thinking_text.clear()

        board = self.board_widget.board
        try:
            move = chess.Move.from_uci(uci_move)
            san = board.san(move)
        except Exception:
            san = uci_move

        self._move_history.append({
            "uci": uci_move,
            "san": san,
            "color": "white" if board.turn == chess.WHITE else "black",
            "reasoning": "",
        })
        self._update_history_display()
        self._update_status()

        if board.is_game_over():
            self._update_status()
            return

        if board.turn != self.board_widget._player_color:
            self._request_llm_move(board.turn)

    def _request_llm_move(self, color: chess.Color):
        """请求指定颜色方的 LLM 走棋"""
        board = self.board_widget.board

        if board.is_game_over():
            return

        legal_moves = self.board_widget.get_legal_moves_uci()
        if not legal_moves:
            return

        connector = self._get_connector_for_color(color)
        side_name = tr("white") if color == chess.WHITE else tr("black")
        model_name = self._get_config_for_color(color).model

        self.status_label.setText(tr("status_thinking", side=side_name, model=model_name))
        self.board_widget.setEnabled(False)
        self.new_game_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.undo_btn.setEnabled(False)
        if hasattr(self, 'color_combo'):
            self.color_combo.setEnabled(False)
        self.mode_combo.setEnabled(False)
        self.step_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)

        QApplication.processEvents()

        side = "white" if color == chess.WHITE else "black"
        self._worker_thread = QThread()
        self._worker = LLMWorker(connector, board.fen(), legal_moves, side)
        self._worker.moveToThread(self._worker_thread)

        self._worker.finished.connect(self._on_llm_move)
        self._worker.error.connect(self._on_llm_error)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)

        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    def _on_llm_move(self, response: LLMResponse):
        move_uci = response.move
        color = self.board_widget.board.turn
        side_name = tr("white") if color == chess.WHITE else tr("black")

        if move_uci:
            try:
                move = chess.Move.from_uci(move_uci)
                san = self.board_widget.board.san(move)
            except Exception:
                san = move_uci

            self._move_history.append({
                "uci": move_uci,
                "san": san,
                "color": "white" if color == chess.WHITE else "black",
                "reasoning": response.reasoning or "",
                "raw": response.raw or "",
                "used_fallback": response.used_fallback,
            })

            self.board_widget.LLM_play_move(move_uci)
            self._update_history_display()
            self._append_thinking(side_name, response)

        self._cleanup_worker()

        # 根据模式决定下一步
        if self._mode == MODE_AI_VS_AI:
            self._restore_ui()
            self._update_status()
            if not self.board_widget.board.is_game_over():
                if self._ai_vs_ai_paused:
                    self.step_btn.setEnabled(True)
                else:
                    delay = self.speed_slider.value()
                    QTimer.singleShot(delay, self._ai_vs_ai_step)
        else:
            self._restore_ui()
            self._update_status()
            if self.board_widget.board.is_game_over():
                return
            if self.board_widget.board.turn == self.board_widget._player_color:
                self.board_widget.setEnabled(True)
            else:
                self._request_llm_move(self.board_widget.board.turn)

    def _on_llm_error(self, error_msg: str):
        self._restore_ui()
        self._cleanup_worker()

        QMessageBox.warning(
            self, tr("error_ai_title"),
            tr("error_ai_body", error=error_msg)
        )
        self.status_label.setText(tr("error_status", error=error_msg[:100]))
        self._ai_vs_ai_active = False

    def _restore_ui(self):
        self.board_widget.setEnabled(True)
        self.new_game_btn.setEnabled(True)
        self.settings_btn.setEnabled(True)
        self.undo_btn.setEnabled(True)
        if hasattr(self, 'color_combo'):
            self.color_combo.setEnabled(True)
        self.mode_combo.setEnabled(True)
        self.step_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        self.thinking_text.setEnabled(True)

    def _cleanup_worker(self):
        if self._worker_thread is not None:
            try:
                self._worker_thread.quit()
                self._worker_thread.wait(3000)
            except RuntimeError:
                pass
        self._worker_thread = None
        self._worker = None

    # ------------------------------------------------------------------
    # AI vs AI 控制
    # ------------------------------------------------------------------

    def _ai_vs_ai_step(self):
        if self._mode != MODE_AI_VS_AI or not self._ai_vs_ai_active:
            return
        if self.board_widget.board.is_game_over():
            return
        if self._worker_thread is not None:
            return

        color = self.board_widget.board.turn
        self._request_llm_move(color)

    def _toggle_ai_vs_ai_pause(self):
        self._ai_vs_ai_paused = not self._ai_vs_ai_paused
        if self._ai_vs_ai_paused:
            self.pause_btn.setText(tr("btn_resume"))
        else:
            self.pause_btn.setText(tr("btn_pause"))
            if not self.board_widget.board.is_game_over():
                QTimer.singleShot(100, self._ai_vs_ai_step)

    # ------------------------------------------------------------------
    # 思考显示
    # ------------------------------------------------------------------

    def _append_thinking(self, side_name: str, response: LLMResponse):
        """把 AI 的思考追加到思考面板"""
        config = self._get_config_for_color(
            chess.WHITE if side_name == tr("white") else chess.BLACK
        )

        header = tr("thinking_header", side=side_name, model=config.model) + "\n"
        move_line = tr("thinking_move", move=response.move)
        if response.used_fallback:
            move_line += tr("thinking_fallback")
        move_line += "\n"

        reasoning = response.reasoning or tr("thinking_no_reasoning")
        if len(reasoning) > 800:
            reasoning = reasoning[:800] + "..."

        if side_name == tr("white"):
            color = "#89B4FA"
        else:
            color = "#F38BA8"

        html = (
            f'<div style="margin-bottom: 10px;">'
            f'<div style="color: {color}; font-weight: bold;">{header}</div>'
            f'<div style="color: #CDD6F4; margin: 4px 0;">'
            f'{self._html_escape(move_line)}</div>'
            f'<div style="color: #A6ADC8; font-style: italic;">'
            f'{self._html_escape(reasoning)}</div>'
            f'</div>'
        )
        self.thinking_text.append(html)

    @staticmethod
    def _html_escape(text: str) -> str:
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\n", "<br>"))

    # ------------------------------------------------------------------
    # 状态/历史显示
    # ------------------------------------------------------------------

    def _update_status(self):
        board = self.board_widget.board
        self.fen_label.setText(f"{tr('fen_label')} {board.fen()}")

        if board.is_game_over():
            result = board.result()
            if result == "1-0":
                msg = tr("game_over_white_wins")
            elif result == "0-1":
                msg = tr("game_over_black_wins")
            elif result == "1/2-1/2":
                msg = tr("game_over_draw")
            else:
                msg = tr("game_over_result", result=result)

            if board.is_checkmate():
                msg += tr("end_checkmate")
            elif board.is_stalemate():
                msg += tr("end_stalemate")
            elif board.is_insufficient_material():
                msg += tr("end_insufficient")
            elif board.is_fifty_moves():
                msg += tr("end_fifty_moves")
            elif board.is_repetition():
                msg += tr("end_repetition")

            self.status_label.setText(msg)
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self._ai_vs_ai_active = False
        elif board.is_check():
            side = tr("white") if board.turn == chess.WHITE else tr("black")
            self.status_label.setText(tr("status_check", side=side))
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            if self._mode == MODE_AI_VS_AI:
                side = tr("white") if board.turn == chess.WHITE else tr("black")
                model = self._get_config_for_color(board.turn).model
                self.status_label.setText(tr("status_to_move", side=side, model=model))
                self.status_label.setStyleSheet("color: #89B4FA; font-weight: normal;")
            else:
                turn = tr("your") if board.turn == self.board_widget._player_color else tr("ai")
                color_name = tr("white") if board.turn == chess.WHITE else tr("black")
                self.status_label.setText(tr("status_your_turn" if turn == tr("your") else "status_ai_turn", color=color_name))
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: normal;")

    def _update_history_display(self):
        lines = []
        move_num = 1
        current_white_move = None
        current_white_num = 0

        for entry in self._move_history:
            color = entry.get("color", "white")
            san = entry.get("san", entry.get("uci", ""))
            uci = entry.get("uci", "")
            used_fb = entry.get("used_fallback", False)

            prefix = "?" if used_fb else ""

            if color == "white":
                if current_white_move is not None:
                    lines.append(
                        f"{current_white_num}. {current_white_move}  {prefix}{san}"
                    )
                    current_white_move = None
                else:
                    current_white_move = prefix + san
                    current_white_num = move_num
            else:
                if current_white_move is not None:
                    lines.append(
                        f"{current_white_num}. {current_white_move}  {prefix}{san}"
                    )
                    current_white_move = None
                    move_num += 1
                else:
                    lines.append(f"{move_num}. ... {prefix}{san}")
                    move_num += 1

        if current_white_move is not None:
            lines.append(f"{current_white_num}. {current_white_move}")

        self.move_history_text.setPlainText("\n".join(lines))
        cursor = self.move_history_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.move_history_text.setTextCursor(cursor)

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _get_config_for_color(self, color: chess.Color) -> LLMConfig:
        if self._mode == MODE_AI_VS_AI:
            return self._config_white if color == chess.WHITE else self._config_black
        player_color = self.board_widget._player_color
        if player_color is None:
            return self._config_white
        if player_color == chess.WHITE:
            return self._config_black
        else:
            return self._config_white

    def _get_connector_for_color(self, color: chess.Color) -> LLMConnector:
        if self._mode == MODE_AI_VS_AI:
            return self._connector_white if color == chess.WHITE else self._connector_black
        player_color = self.board_widget._player_color
        if player_color == chess.WHITE:
            return self._connector_black
        return self._connector_white

    def _undo_move(self):
        if self._mode == MODE_AI_VS_AI:
            return
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
            self.thinking_text.clear()

    def _open_settings(self):
        dlg = SettingsDialog(self._config_white, self)
        dlg.set_test_callback(lambda: self._test_connection(dlg))
        dlg.config_black = self._config_black
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            self._config_white = dlg.get_config()
            self._config_black = getattr(dlg, 'config_black', LLMConfig())
            self._config = self._config_white
            self._connector_white = LLMConnector(self._config_white)
            self._connector_black = LLMConnector(self._config_black)

            # 检查语言是否改变
            new_lang = dlg.get_language()
            if new_lang != get_language():
                set_language(new_lang)
                self._update_ui_language()

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
        self._connector_white.close()
        self._connector_black.close()
        super().closeEvent(event)
