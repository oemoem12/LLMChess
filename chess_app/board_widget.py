import chess
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QFont, QMouseEvent, QPen, QBrush


PIECE_UNICODE = {
    chess.KING:   ("\u2654", "\u265a"),
    chess.QUEEN:  ("\u2655", "\u265b"),
    chess.ROOK:   ("\u2656", "\u265c"),
    chess.BISHOP: ("\u2657", "\u265d"),
    chess.KNIGHT: ("\u2658", "\u265e"),
    chess.PAWN:   ("\u2659", "\u265f"),
}

LIGHT_SQUARE = QColor("#F0D9B5")
DARK_SQUARE = QColor("#B58863")
SELECTED_COLOR = QColor("#829769")
LEGAL_MOVE_COLOR = QColor("#82976955")
LEGAL_MOVE_DOT_COLOR = QColor("#829769aa")
LAST_MOVE_COLOR = QColor("#CDD26A")
CHECK_COLOR = QColor("#FF6B6B")
BORDER_COLOR = QColor("#4A4A4A")


class PromotionDialog(QDialog):
    def __init__(self, color: chess.Color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Promote Pawn")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.piece_type = chess.QUEEN

        layout = QHBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        pieces = [
            (chess.QUEEN, "Q"),
            (chess.ROOK, "R"),
            (chess.BISHOP, "B"),
            (chess.KNIGHT, "N"),
        ]

        for pt, label in pieces:
            piece_char = PIECE_UNICODE[pt][0 if color == chess.WHITE else 1]
            btn = QPushButton(piece_char)
            btn.setFont(QFont("Segoe UI Symbol", 28))
            btn.setFixedSize(52, 52)
            btn.clicked.connect(lambda checked, p=pt: self._select(p))
            layout.addWidget(btn)

    def _select(self, piece_type: chess.PieceType):
        self.piece_type = piece_type
        self.accept()


class ChessBoardWidget(QWidget):
    move_made = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self._flipped = False
        self._selected_square: int | None = None
        self._legal_moves: list[chess.Move] = []
        self._last_move: chess.Move | None = None
        self._player_color = chess.WHITE
        self._human_turn = True

        self.setMinimumSize(480, 480)
        self.setMouseTracking(False)

    @property
    def square_size(self) -> int:
        return min(self.width(), self.height()) // 8

    @property
    def board_offset_x(self) -> int:
        return (self.width() - self.square_size * 8) // 2

    @property
    def board_offset_y(self) -> int:
        return (self.height() - self.square_size * 8) // 2

    def set_player_color(self, color: chess.Color):
        self._player_color = color
        self._flipped = (color == chess.BLACK)
        self._human_turn = (self.board.turn == self._player_color)
        self.update()

    def set_position(self, fen: str):
        self.board = chess.Board(fen)
        self._selected_square = None
        self._legal_moves = []
        self._last_move = None
        self._human_turn = (self.board.turn == self._player_color)
        self.update()

    def apply_move(self, move: chess.Move):
        self._last_move = move
        self.board.push(move)
        self._selected_square = None
        self._legal_moves = []
        self._human_turn = (self.board.turn == self._player_color)
        self.update()

    def get_legal_moves_uci(self) -> list[str]:
        return [move.uci() for move in self.board.legal_moves]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        sq_size = self.square_size
        ox = self.board_offset_x
        oy = self.board_offset_y

        for row in range(8):
            for col in range(8):
                x = ox + col * sq_size
                y = oy + row * sq_size

                display_row = 7 - row if not self._flipped else row
                display_col = col if not self._flipped else 7 - col

                is_light = (display_row + display_col) % 2 == 0
                color = LIGHT_SQUARE if is_light else DARK_SQUARE

                painter.fillRect(QRect(x, y, sq_size, sq_size), color)

        if self._selected_square is not None:
            sel_col = chess.square_file(self._selected_square)
            sel_row = chess.square_rank(self._selected_square)

            if self._flipped:
                sel_col = 7 - sel_col
            else:
                sel_row = 7 - sel_row

            sx = ox + sel_col * sq_size
            sy = oy + sel_row * sq_size

            painter.fillRect(QRect(sx, sy, sq_size, sq_size), SELECTED_COLOR)

            for move in self._legal_moves:
                if move.from_square != self._selected_square:
                    continue

                to_sq = move.to_square
                to_col = chess.square_file(to_sq)
                to_row = chess.square_rank(to_sq)

                if self._flipped:
                    to_col = 7 - to_col
                else:
                    to_row = 7 - to_row

                tx = ox + to_col * sq_size
                ty = oy + to_row * sq_size

                target_piece = self.board.piece_at(to_sq)
                if target_piece is not None:
                    painter.setPen(QPen(LEGAL_MOVE_COLOR, 3))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(QRect(tx + 2, ty + 2, sq_size - 4, sq_size - 4))
                else:
                    dot_size = sq_size // 4
                    dx = tx + (sq_size - dot_size) // 2
                    dy = ty + (sq_size - dot_size) // 2
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(LEGAL_MOVE_DOT_COLOR))
                    painter.drawEllipse(QRect(dx, dy, dot_size, dot_size))

        if self._last_move is not None:
            for sq in (self._last_move.from_square, self._last_move.to_square):
                col = chess.square_file(sq)
                row = chess.square_rank(sq)

                if self._flipped:
                    col = 7 - col
                else:
                    row = 7 - row

                lx = ox + col * sq_size
                ly = oy + row * sq_size

                painter.fillRect(QRect(lx, ly, sq_size, sq_size), LAST_MOVE_COLOR)

        king_sq = self.board.king(self.board.turn)
        if king_sq is not None and self.board.is_check():
            col = chess.square_file(king_sq)
            row = chess.square_rank(king_sq)

            if self._flipped:
                col = 7 - col
            else:
                row = 7 - row

            kx = ox + col * sq_size
            ky = oy + row * sq_size

            painter.fillRect(QRect(kx, ky, sq_size, sq_size), CHECK_COLOR)

        piece_font = QFont("Segoe UI Symbol", int(sq_size * 0.72))
        painter.setFont(piece_font)
        painter.setPen(QColor("#302E2B"))

        for row in range(8):
            for col in range(8):
                display_row = 7 - row if not self._flipped else row
                display_col = col if not self._flipped else 7 - col

                square = chess.square(display_col, display_row)
                piece = self.board.piece_at(square)
                if piece is None:
                    continue

                x = ox + col * sq_size
                y = oy + row * sq_size

                is_white = piece.color == chess.WHITE
                ptype = piece.piece_type
                symbol = PIECE_UNICODE[ptype][0 if is_white else 1]

                if is_white:
                    painter.setPen(QColor("#FFFFFF"))
                    shadow_offset = max(1, sq_size // 40)
                    painter.drawText(QRect(x + shadow_offset, y + shadow_offset, sq_size, sq_size),
                                     Qt.AlignmentFlag.AlignCenter, symbol)
                    painter.setPen(QColor("#302E2B"))
                else:
                    painter.setPen(QColor("#302E2B"))

                painter.drawText(QRect(x, y, sq_size, sq_size),
                                 Qt.AlignmentFlag.AlignCenter, symbol)

        painter.setPen(QPen(BORDER_COLOR, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRect(ox, oy, sq_size * 8, sq_size * 8))

        coord_font = QFont("Segoe UI", max(8, sq_size // 6))
        painter.setFont(coord_font)
        painter.setPen(QColor("#4A4A4A"))

        files = "abcdefgh"
        ranks = "12345678"

        for i in range(8):
            display_file = files[7 - i if self._flipped else i]
            display_rank = ranks[i if self._flipped else 7 - i]

            fx = ox + i * sq_size + 3
            fy = oy + 8 * sq_size - 2
            painter.drawText(QRect(fx, fy, sq_size, sq_size // 4),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                             display_file)

            rx = ox - sq_size // 4
            ry = oy + i * sq_size
            painter.drawText(QRect(rx, ry, sq_size // 4, sq_size),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             display_rank)

        if self.board.is_game_over():
            result = self.board.result()
            painter.setFont(QFont("Segoe UI", max(16, sq_size // 2)))
            painter.setPen(QPen(QColor("#FFFFFF")))
            painter.fillRect(QRect(ox, oy + sq_size * 3, sq_size * 8, sq_size * 2),
                             QColor(0, 0, 0, 180))

            outcome_text = "Game Over"
            if result == "1-0":
                outcome_text = "White Wins!"
            elif result == "0-1":
                outcome_text = "Black Wins!"
            elif result == "1/2-1/2":
                outcome_text = "Draw!"

            painter.drawText(QRect(ox, oy + sq_size * 3, sq_size * 8, sq_size * 2),
                             Qt.AlignmentFlag.AlignCenter, outcome_text)

    def mousePressEvent(self, event: QMouseEvent):
        if not self._human_turn or self.board.is_game_over():
            return

        sq_size = self.square_size
        ox = self.board_offset_x
        oy = self.board_offset_y

        col = (event.pos().x() - ox) // sq_size
        row = (event.pos().y() - oy) // sq_size

        if col < 0 or col >= 8 or row < 0 or row >= 8:
            return

        if self._flipped:
            file_idx = 7 - col
            rank_idx = row
        else:
            file_idx = col
            rank_idx = 7 - row

        clicked_square = chess.square(file_idx, rank_idx)

        if self._selected_square is None:
            piece = self.board.piece_at(clicked_square)
            if piece is not None and piece.color == self._player_color:
                self._selected_square = clicked_square
                self._legal_moves = [
                    move for move in self.board.legal_moves
                    if move.from_square == clicked_square
                ]
                self.update()
        else:
            if clicked_square == self._selected_square:
                self._selected_square = None
                self._legal_moves = []
                self.update()
                return

            for move in self._legal_moves:
                if move.to_square == clicked_square:
                    if move.promotion:
                        self._handle_promotion(move, clicked_square)
                    else:
                        self._execute_move(move)
                    return

            piece = self.board.piece_at(clicked_square)
            if piece is not None and piece.color == self._player_color:
                self._selected_square = clicked_square
                self._legal_moves = [
                    move for move in self.board.legal_moves
                    if move.from_square == clicked_square
                ]
                self.update()
            else:
                self._selected_square = None
                self._legal_moves = []
                self.update()

    def _handle_promotion(self, move: chess.Move, to_square: chess.Square):
        dlg = PromotionDialog(self._player_color, self)
        sq_size = self.square_size
        ox = self.board_offset_x
        oy = self.board_offset_y

        if self._flipped:
            col = 7 - chess.square_file(to_square)
            row = chess.square_rank(to_square)
        else:
            col = chess.square_file(to_square)
            row = 7 - chess.square_rank(to_square)

        dlg_x = self.mapToGlobal(
            self.rect().topLeft()
        ).x() + ox + col * sq_size + sq_size
        dlg_y = self.mapToGlobal(
            self.rect().topLeft()
        ).y() + oy + row * sq_size
        dlg.move(dlg_x + 10, dlg_y)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            promotion_move = chess.Move(
                move.from_square, move.to_square, promotion=dlg.piece_type
            )
            self._execute_move(promotion_move)
        else:
            self._selected_square = None
            self._legal_moves = []
            self.update()

    def _execute_move(self, move: chess.Move):
        self.apply_move(move)
        self.move_made.emit(move.uci())

    def LLM_play_move(self, uci_move: str):
        try:
            move = chess.Move.from_uci(uci_move)
        except ValueError:
            return

        if move in self.board.legal_moves:
            self.apply_move(move)