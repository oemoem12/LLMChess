import chess
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QSpinBox,
    QDoubleSpinBox, QDialogButtonBox, QVBoxLayout, QGroupBox,
    QHBoxLayout, QPushButton, QLabel,
)
from PyQt6.QtCore import Qt

from chess_app.llm_connector import LLMConfig


PRESET_CONFIGS = {
    "Ollama (Default)": LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434/v1",
        model="qwen2.5:7b",
        api_key="",
        temperature=0.3,
        max_tokens=512,
    ),
    "llama.cpp Server": LLMConfig(
        provider="llamacpp",
        base_url="http://localhost:8080/v1",
        model="llama",
        api_key="",
        temperature=0.3,
        max_tokens=512,
    ),
    "LM Studio": LLMConfig(
        provider="lmstudio",
        base_url="http://localhost:1234/v1",
        model="local-model",
        api_key="",
        temperature=0.3,
        max_tokens=512,
    ),
    "Custom": LLMConfig(
        provider="custom",
        base_url="http://localhost:8000/v1",
        model="",
        api_key="",
        temperature=0.3,
        max_tokens=512,
    ),
}


class SettingsDialog(QDialog):
    def __init__(self, current_config: LLMConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM Connection Settings")
        self.setMinimumWidth(480)
        self._current_config = current_config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        preset_group = QGroupBox("Preset Configuration")
        preset_layout = QVBoxLayout(preset_group)

        self.preset_combo = QComboBox()
        for name in PRESET_CONFIGS:
            self.preset_combo.addItem(name)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)

        layout.addWidget(preset_group)

        settings_group = QGroupBox("Connection Settings")
        form = QFormLayout(settings_group)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama", "llamacpp", "lmstudio", "custom"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form.addRow("Provider:", self.provider_combo)

        self.base_url_edit = QLineEdit()
        form.addRow("Base URL:", self.base_url_edit)

        self.model_edit = QLineEdit()
        form.addRow("Model Name:", self.model_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("(leave empty if not needed)")
        form.addRow("API Key:", self.api_key_edit)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        form.addRow("Temperature:", self.temperature_spin)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(16, 4096)
        form.addRow("Max Tokens:", self.max_tokens_spin)

        layout.addWidget(settings_group)

        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.test_status = QLabel("")
        self.test_status.setWordWrap(True)
        test_layout.addWidget(self.test_btn)
        test_layout.addWidget(self.test_status, 1)
        layout.addLayout(test_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._apply_config(self._current_config)

    def _apply_config(self, config: LLMConfig):
        self.provider_combo.setCurrentText(config.provider)
        self.base_url_edit.setText(config.base_url)
        self.model_edit.setText(config.model)
        self.api_key_edit.setText(config.api_key)
        self.temperature_spin.setValue(config.temperature)
        self.max_tokens_spin.setValue(config.max_tokens)

    def _on_preset_changed(self, name: str):
        if name in PRESET_CONFIGS and name != "Custom":
            self._apply_config(PRESET_CONFIGS[name])

    def _on_provider_changed(self, provider: str):
        preset_map = {
            "ollama": "Ollama (Default)",
            "llamacpp": "llama.cpp Server",
            "lmstudio": "LM Studio",
        }
        if provider in preset_map and preset_map[provider] in PRESET_CONFIGS:
            self._apply_config(PRESET_CONFIGS[preset_map[provider]])

    def get_config(self) -> LLMConfig:
        return LLMConfig(
            provider=self.provider_combo.currentText(),
            base_url=self.base_url_edit.text().strip(),
            model=self.model_edit.text().strip(),
            api_key=self.api_key_edit.text().strip(),
            temperature=self.temperature_spin.value(),
            max_tokens=self.max_tokens_spin.value(),
        )

    def set_test_callback(self, callback):
        self.test_btn.clicked.connect(callback)

    def set_test_status(self, success: bool, message: str):
        color = "#4CAF50" if success else "#F44336"
        self.test_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.test_status.setText(message)