from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QSpinBox,
    QDoubleSpinBox, QDialogButtonBox, QVBoxLayout, QGroupBox,
    QHBoxLayout, QPushButton, QLabel, QTabWidget, QWidget,
)
from PyQt6.QtCore import Qt

from chess_app.llm_connector import LLMConfig, PERSONAS


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


class LLMConfigWidget(QWidget):
    """单侧 LLM 配置面板（白方或黑方）"""

    def __init__(self, config: LLMConfig, side_name: str = "LLM"):
        super().__init__()
        self._side_name = side_name
        layout = QVBoxLayout(self)

        # 预设
        preset_group = QGroupBox("Preset Configuration")
        preset_layout = QVBoxLayout(preset_group)
        self.preset_combo = QComboBox()
        for name in PRESET_CONFIGS:
            self.preset_combo.addItem(name)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        layout.addWidget(preset_group)

        # 连接设置
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

        # 人设
        self.persona_combo = QComboBox()
        for name in PERSONAS:
            self.persona_combo.addItem(name.title(), name)
        form.addRow("AI Persona:", self.persona_combo)

        layout.addWidget(settings_group)

        self._apply_config(config)

    def _apply_config(self, config: LLMConfig):
        self.provider_combo.setCurrentText(config.provider)
        self.base_url_edit.setText(config.base_url)
        self.model_edit.setText(config.model)
        self.api_key_edit.setText(config.api_key)
        self.temperature_spin.setValue(config.temperature)
        self.max_tokens_spin.setValue(config.max_tokens)
        # 人设
        if config.persona and config.persona in PERSONAS:
            idx = self.persona_combo.findData(config.persona)
            if idx >= 0:
                self.persona_combo.setCurrentIndex(idx)
        else:
            self.persona_combo.setCurrentIndex(0)  # default

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
            persona=self.persona_combo.currentData() or "default",
        )


class SettingsDialog(QDialog):
    def __init__(self, current_config: LLMConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM Connection Settings")
        self.setMinimumWidth(560)
        self.setMinimumHeight(560)
        self._current_config = current_config
        self.config_black = LLMConfig()  # 默认黑方配置
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Tab 切换白方/黑方配置（AI vs AI 模式用）
        self.tabs = QTabWidget()

        # 白方 Tab
        self.white_widget = LLMConfigWidget(self._current_config, "White")
        self.tabs.addTab(self.white_widget, "⬜ White (Player 1)")

        # 黑方 Tab
        self.black_widget = LLMConfigWidget(self.config_black, "Black")
        self.tabs.addTab(self.black_widget, "⬛ Black (Player 2)")

        layout.addWidget(self.tabs)

        # 测试
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout(test_group)

        test_btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Current Tab")
        self.test_btn.clicked.connect(self._on_test_current)
        test_btn_layout.addWidget(self.test_btn)
        test_layout.addLayout(test_btn_layout)

        self.test_status = QLabel("")
        self.test_status.setWordWrap(True)
        self.test_status.setMinimumHeight(40)
        test_layout.addWidget(self.test_status)

        layout.addWidget(test_group)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_test_current(self):
        config = self.get_config()
        from chess_app.llm_connector import LLMConnector
        connector = LLMConnector(config)
        try:
            success, message = connector.test_connection()
            self.set_test_status(success, message)
        except Exception as e:
            self.set_test_status(False, str(e))
        finally:
            connector.close()

    def get_config(self) -> LLMConfig:
        """获取当前 Tab 的配置"""
        if self.tabs.currentIndex() == 0:
            return self.white_widget.get_config()
        return self.black_widget.get_config()

    def set_test_callback(self, callback):
        """兼容旧 API（已内置 _on_test_current，可忽略）"""
        pass

    def set_test_status(self, success: bool, message: str):
        color = "#4CAF50" if success else "#F44336"
        self.test_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.test_status.setText(message)
