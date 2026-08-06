import sys
import os

__version__ = "1.5.6"


def main():
    from PyQt6.QtWidgets import QApplication

    os.environ["QT_QPA_PLATFORM"] = "xcb"

    from chess_app.game_controller import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("LLM Chess")
    app.setOrganizationName("LLMChess")
    app.setStyle("Fusion")

    app.setStyleSheet("""
        QMainWindow { background-color: #1E1E2E; }
        QGroupBox {
            color: #CDD6F4; font-weight: bold;
            border: 1px solid #45475A; border-radius: 6px;
            margin-top: 12px; padding-top: 14px;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QPushButton {
            background-color: #585B70; color: #CDD6F4;
            border: 1px solid #585B70; border-radius: 4px;
            padding: 6px 16px; font-weight: bold;
        }
        QPushButton:hover { background-color: #6C7086; }
        QPushButton:pressed { background-color: #45475A; }
        QPushButton:disabled { background-color: #313244; color: #6C7086; }
        QComboBox {
            background-color: #313244; color: #CDD6F4;
            border: 1px solid #45475A; border-radius: 4px; padding: 4px 8px;
        }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background-color: #313244; color: #CDD6F4;
            selection-background-color: #585B70;
        }
        QLabel { color: #CDD6F4; }
        QTextEdit {
            background-color: #313244; color: #CDD6F4;
            border: 1px solid #45475A; border-radius: 4px;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox {
            background-color: #313244; color: #CDD6F4;
            border: 1px solid #45475A; border-radius: 4px; padding: 4px;
        }
        QDialog { background-color: #1E1E2E; }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())