"""
Settings Dialog - LLM 连接设置
支持白方/黑方独立配置，语言切换，云端 API 预设
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QSpinBox,
    QDoubleSpinBox, QDialogButtonBox, QVBoxLayout, QGroupBox,
    QHBoxLayout, QPushButton, QLabel, QTabWidget, QWidget,
)
from PyQt6.QtCore import Qt

from chess_app.llm_connector import LLMConfig, PERSONAS, PRESET_CONFIGS
from chess_app.i18n import tr, get_language, set_language


class LLMConfigWidget(QWidget):
    """单侧 LLM 配置面板（白方或黑方）"""

    def __init__(self, config: LLMConfig, side_name: str = "LLM"):
        super().__init__()
        self._side_name = side_name
        layout = QVBoxLayout(self)

        # 预设
        preset_group = QGroupBox(tr("settings_preset_group"))
        preset_layout = QVBoxLayout(preset_group)
        self.preset_combo = QComboBox()
        self.preset_combo.addItem(tr("preset_ollama"), "ollama")
        self.preset_combo.addItem(tr("preset_llamacpp"), "llamacpp")
        self.preset_combo.addItem(tr("preset_lmstudio"), "lmstudio")
        self.preset_combo.addItem(tr("preset_openai"), "openai")
        self.preset_combo.addItem(tr("preset_deepseek"), "deepseek")
        self.preset_combo.addItem(tr("preset_custom"), "custom")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        layout.addWidget(preset_group)

        # 连接设置
        settings_group = QGroupBox(tr("settings_connection_group"))
        form = QFormLayout(settings_group)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama", "llamacpp", "lmstudio", "openai", "deepseek", "custom"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form.addRow(tr("settings_provider"), self.provider_combo)

        self.base_url_edit = QLineEdit()
        form.addRow(tr("settings_base_url"), self.base_url_edit)

        self.model_edit = QLineEdit()
        form.addRow(tr("settings_model"), self.model_edit)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText(tr("settings_api_key_hint"))
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(tr("settings_api_key"), self.api_key_edit)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        form.addRow(tr("settings_temperature"), self.temperature_spin)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(16, 4096)
        form.addRow(tr("settings_max_tokens"), self.max_tokens_spin)

        # 人设
        self.persona_combo = QComboBox()
        self.persona_combo.addItem(tr("persona_default"), "default")
        self.persona_combo.addItem(tr("persona_aggressive"), "aggressive")
        self.persona_combo.addItem(tr("persona_defensive"), "defensive")
        self.persona_combo.addItem(tr("persona_creative"), "creative")
        self.persona_combo.addItem(tr("persona_teacher"), "teacher")
        form.addRow(tr("settings_persona"), self.persona_combo)

        layout.addWidget(settings_group)

        self._apply_config(config)

    def _apply_config(self, config: LLMConfig):
        self.provider_combo.setCurrentText(config.provider)
        self.base_url_edit.setText(config.base_url)
        self.model_edit.setText(config.model)
        self.api_key_edit.setText(config.api_key)
        self.temperature_spin.setValue(config.temperature)
        self.max_tokens_spin.setValue(config.max_tokens)
        if config.persona and config.persona in PERSONAS:
            idx = self.persona_combo.findData(config.persona)
            if idx >= 0:
                self.persona_combo.setCurrentIndex(idx)
        else:
            self.persona_combo.setCurrentIndex(0)

    def _on_preset_changed(self):
        preset_key = self.preset_combo.currentData()
        if preset_key and preset_key in PRESET_CONFIGS:
            self._apply_config(LLMConfig(**PRESET_CONFIGS[preset_key]))

    def _on_provider_changed(self, provider: str):
        if provider in PRESET_CONFIGS:
            self._apply_config(LLMConfig(**PRESET_CONFIGS[provider]))

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
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(560)
        self.setMinimumHeight(600)
        self._current_config = current_config
        self.config_black = LLMConfig()
        self._language = get_language()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 语言选择
        lang_group = QGroupBox(tr("settings_language"))
        lang_layout = QHBoxLayout(lang_group)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem(tr("settings_language_en"), "en")
        self.lang_combo.addItem(tr("settings_language_zh"), "zh")
        idx = self.lang_combo.findData(self._language)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        layout.addWidget(lang_group)

        # Tab 切换白方/黑方配置
        self.tabs = QTabWidget()

        self.white_widget = LLMConfigWidget(self._current_config, "White")
        self.tabs.addTab(self.white_widget, tr("settings_tab_white"))

        self.black_widget = LLMConfigWidget(self.config_black, "Black")
        self.tabs.addTab(self.black_widget, tr("settings_tab_black"))

        layout.addWidget(self.tabs)

        # 测试
        test_group = QGroupBox(tr("settings_test_group"))
        test_layout = QVBoxLayout(test_group)

        test_btn_layout = QHBoxLayout()
        self.test_btn = QPushButton(tr("settings_test_btn"))
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

    def _on_language_changed(self):
        """语言切换预览（不立即应用，等用户点 OK 才生效）"""
        new_lang = self.lang_combo.currentData()
        if new_lang and new_lang != self._language:
            # 只更新当前对话框的 UI 文本作为预览
            self.setWindowTitle(tr("settings_title"))
            self.tabs.setTabText(0, tr("settings_tab_white"))
            self.tabs.setTabText(1, tr("settings_tab_black"))
            self.test_btn.setText(tr("settings_test_btn"))
            # 注意：不调用 set_language()，等用户点 OK 后才全局生效

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
        """返回当前 tab 的配置（向后兼容）"""
        if self.tabs.currentIndex() == 0:
            return self.white_widget.get_config()
        return self.black_widget.get_config()

    def get_white_config(self) -> LLMConfig:
        """返回白方配置"""
        return self.white_widget.get_config()

    def get_black_config(self) -> LLMConfig:
        """返回黑方配置"""
        return self.black_widget.get_config()

    def get_language(self) -> str:
        return self._language

    def set_test_callback(self, callback):
        pass

    def set_test_status(self, success: bool, message: str):
        color = "#4CAF50" if success else "#F44336"
        self.test_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.test_status.setText(message)
