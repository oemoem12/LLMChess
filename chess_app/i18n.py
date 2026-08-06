"""
i18n - 国际化/本地化支持
支持中文 (zh) 和英文 (en)
"""

# 所有 UI 文本的翻译表
TRANSLATIONS = {
    # --- 主窗口标题 ---
    "app_title": {
        "en": "LLM Chess - AI Opponent",
        "zh": "LLM Chess - AI 对手",
    },

    # --- 模式选择 ---
    "mode_group": {"en": "Game Mode", "zh": "游戏模式"},
    "mode_human_vs_ai": {"en": "👤 Human vs AI", "zh": "👤 人机对弈"},
    "mode_ai_vs_ai": {"en": "🤖 AI vs AI (Watch)", "zh": "🤖 AI 对弈（观战）"},
    "color_white_first": {"en": "White (You go first)", "zh": "白方（你先走）"},
    "color_black_first": {"en": "Black (AI goes first)", "zh": "黑方（AI 先走）"},

    # --- 按钮 ---
    "btn_new_game": {"en": "New Game", "zh": "新局"},
    "btn_settings": {"en": "Settings...", "zh": "设置..."},
    "btn_pause": {"en": "⏸ Pause", "zh": "⏸ 暂停"},
    "btn_resume": {"en": "▶ Resume", "zh": "▶ 继续"},
    "btn_step": {"en": "⏭ Step", "zh": "⏭ 单步"},
    "btn_undo": {"en": "Undo Last Move", "zh": "悔棋"},

    # --- 面板标题 ---
    "group_move_history": {"en": "Move History", "zh": "走棋历史"},
    "group_ai_thinking": {"en": "AI Thinking", "zh": "AI 思考"},
    "group_game_status": {"en": "Game Status", "zh": "游戏状态"},
    "group_ai_vs_ai_speed": {"en": "AI vs AI Speed", "zh": "AI 对弈速度"},
    "label_delay": {"en": "Delay:", "zh": "延迟："},

    # --- 状态文本 ---
    "status_ready": {"en": "Ready. Make your move.", "zh": "准备就绪，请走棋。"},
    "status_thinking": {"en": "{side} AI ({model}) is thinking...", "zh": "{side} AI（{model}）正在思考..."},
    "status_to_move": {"en": "{side} AI ({model}) to move...", "zh": "{side} AI（{model}）走棋..."},
    "status_your_turn": {"en": "{color}'s turn (Your turn)", "zh": "{color}方（你的回合）"},
    "status_ai_turn": {"en": "{color}'s turn (AI's turn)", "zh": "{color}方（AI 回合）"},
    "status_check": {"en": "{side} is in check!", "zh": "{side} 被将军！"},

    # --- 游戏结束 ---
    "game_over_white_wins": {"en": "Game Over - White Wins!", "zh": "游戏结束 - 白方胜！"},
    "game_over_black_wins": {"en": "Game Over - Black Wins!", "zh": "游戏结束 - 黑方胜！"},
    "game_over_draw": {"en": "Game Over - It's a Draw!", "zh": "游戏结束 - 和棋！"},
    "game_over_result": {"en": "Game Over - {result}", "zh": "游戏结束 - {result}"},
    "end_checkmate": {"en": " (Checkmate)", "zh": "（将杀）"},
    "end_stalemate": {"en": " (Stalemate)", "zh": "（逼和）"},
    "end_insufficient": {"en": " (Insufficient Material)", "zh": "（子力不足）"},
    "end_fifty_moves": {"en": " (50-Move Rule)", "zh": "（50步规则）"},
    "end_repetition": {"en": " (Threefold Repetition)", "zh": "（三次重复）"},

    # --- AI 思考面板 ---
    "thinking_header": {"en": "━━━ {side} AI ({model}) ━━━", "zh": "━━━ {side} AI（{model}）━━━"},
    "thinking_move": {"en": "➤ Move: {move}", "zh": "➤ 着法：{move}"},
    "thinking_fallback": {"en": "  [fallback]", "zh": "  [回退]"},
    "thinking_no_reasoning": {"en": "(no reasoning provided)", "zh": "（未提供推理）"},
    "thinking_fallback_reason": {"en": "[LLM returned invalid, fell back to first legal move {move}]", "zh": "[LLM 返回无效，已回退到第一个合法着法 {move}]"},

    # --- 错误对话框 ---
    "error_ai_title": {"en": "AI Error", "zh": "AI 错误"},
    "error_ai_body": {"en": "Failed to get move from LLM:\n\n{error}\n\nPlease check your LLM connection settings and ensure the server is running.", "zh": "无法从 LLM 获取着法：\n\n{error}\n\n请检查 LLM 连接设置并确保服务器正在运行。"},
    "error_status": {"en": "Error: {error}", "zh": "错误：{error}"},

    # --- 设置对话框 ---
    "settings_title": {"en": "LLM Connection Settings", "zh": "LLM 连接设置"},
    "settings_tab_white": {"en": "⬜ White (Player 1)", "zh": "⬜ 白方（玩家 1）"},
    "settings_tab_black": {"en": "⬛ Black (Player 2)", "zh": "⬛ 黑方（玩家 2）"},
    "settings_preset_group": {"en": "Preset Configuration", "zh": "预设配置"},
    "settings_connection_group": {"en": "Connection Settings", "zh": "连接设置"},
    "settings_test_group": {"en": "Connection Test", "zh": "连接测试"},
    "settings_test_btn": {"en": "Test Current Tab", "zh": "测试当前配置"},
    "settings_provider": {"en": "Provider:", "zh": "后端："},
    "settings_base_url": {"en": "Base URL:", "zh": "地址："},
    "settings_model": {"en": "Model Name:", "zh": "模型名："},
    "settings_api_key": {"en": "API Key:", "zh": "API 密钥："},
    "settings_api_key_hint": {"en": "(leave empty if not needed)", "zh": "（不需要则留空）"},
    "settings_temperature": {"en": "Temperature:", "zh": "温度："},
    "settings_max_tokens": {"en": "Max Tokens:", "zh": "最大 Token："},
    "settings_persona": {"en": "AI Persona:", "zh": "AI 人设："},
    "settings_language": {"en": "Language:", "zh": "语言："},
    "settings_language_en": {"en": "English", "zh": "英文"},
    "settings_language_zh": {"en": "中文", "zh": "中文"},

    # --- 人设 ---
    "persona_default": {"en": "Default", "zh": "默认"},
    "persona_aggressive": {"en": "Aggressive", "zh": "进攻型"},
    "persona_defensive": {"en": "Defensive", "zh": "防守型"},
    "persona_creative": {"en": "Creative", "zh": "创意型"},
    "persona_teacher": {"en": "Teacher", "zh": "教学型"},

    # --- 预设名 ---
    "preset_ollama": {"en": "Ollama (Default)", "zh": "Ollama（默认）"},
    "preset_llamacpp": {"en": "llama.cpp Server", "zh": "llama.cpp 服务器"},
    "preset_lmstudio": {"en": "LM Studio", "zh": "LM Studio"},
    "preset_openai": {"en": "OpenAI (GPT)", "zh": "OpenAI（GPT）"},
    "preset_deepseek": {"en": "DeepSeek API", "zh": "DeepSeek API"},
    "preset_custom": {"en": "Custom", "zh": "自定义"},

    # --- 通用 ---
    "white": {"en": "White", "zh": "白方"},
    "black": {"en": "Black", "zh": "黑方"},
    "your": {"en": "Your", "zh": "你的"},
    "ai": {"en": "AI", "zh": "AI"},
    "fen_label": {"en": "FEN:", "zh": "FEN："},
}


# 当前语言（默认英文，可通过 set_language 切换）
_current_language = "en"


def set_language(lang: str):
    """切换语言：'en' 或 'zh'"""
    global _current_language
    if lang in ("en", "zh"):
        _current_language = lang


def get_language() -> str:
    return _current_language


def tr(key: str, **kwargs) -> str:
    """获取翻译文本，支持 {placeholder} 替换"""
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_language, entry.get("en", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
