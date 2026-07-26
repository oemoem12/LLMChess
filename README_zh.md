# 用本地大语言模型下国际象棋是什么体验？我开源了一个项目

> 不需要联网、不需要 GPU 云端、不花一分钱——只要一个本地的 Ollama/llama.cpp/LM Studio，就能和 AI 下棋，**或者看两个 AI 互相对战**。

---

## 缘起

一直想和 AI 下国际象棋。Chess.com 上的 Stockfish 太强了（ELO 3700+），虐得我怀疑人生。我想找的是一个**有"思考过程"的 AI**——不是那种冷冰冰的最优解引擎，而是一个能和我"对话式"下棋的对手。

于是我想到了本地大语言模型。

LLM 下棋有天然优势：它能理解局面、能"解释"着法、甚至能给出战略意图。当然，缺点是它经常会走出一些让你摸不着头脑的"创意着法"——但这不正是下棋的乐趣所在吗？

所以我写了 **LLM Chess**——一个用 Python + PyQt6 开发的国际象棋桌面应用，可以连接本地的 LLM 服务，实现**人机对弈**或**AI vs AI 观战**。

---

## 最新版本：v1.5.0

### 🆕 v1.5.0 新增功能

- **🤖 AI vs AI 模式** — 让两个 LLM 互相对弈，白方/黑方可以配置不同的模型/后端
- **💭 AI 思考显示** — 右侧新增"AI Thinking"面板，实时显示 AI 的推理过程
- **🎭 AI 人设系统** — 5 种性格：Default / Aggressive / Defensive / Creative / Teacher
- **⏯ 暂停/单步控制** — AI vs AI 时可暂停、继续、单步推进
- **🎚 速度调节** — 0-5 秒/步可调，方便观察每步推理

---

## 长什么样

打开之后长这样：

- **左侧**：8×8 棋盘，支持点击走棋，合法着法会高亮显示，上一步走法黄色标记，被将军的国王红色警告
- **右侧**：走棋历史（SAN 格式）+ AI 思考显示 + 当前 FEN 状态 + 游戏信息
- **底部**：New Game / Settings / Undo 三个按钮（AI vs AI 模式下变成 Pause/Step）

整体是深色 Catppuccin 风格 UI，不刺眼，看着舒服。

---

## 怎么用

### 前提条件

你需要先有一个本地运行的 LLM 服务，三选一：

| 后端 | 安装方式 | 启动命令 |
|------|----------|----------|
| **Ollama** | 官网下载 | `ollama run qwen2.5:7b` |
| **llama.cpp** | `git clone` + 编译 | `./llama-server -m model.gguf --port 8080` |
| **LM Studio** | 官网下载 | GUI 里开 Local Server |

### 安装 LLM Chess

```bash
pip install llmchess
```

或者 Ubuntu/Debian 用户可以直接下载 DEB 包：

```bash
sudo dpkg -i llmchess_1.0.0_all.deb
```

然后运行：

```bash
llmchess
# 或者 python3 -m llmchess
```

### 连接设置

点 **Settings** → 选你的后端（Ollama/llama.cpp/LM Studio）→ 点 **Test Connection** → 成功！

选 White（你先手）或 Black（AI 先手），然后点棋子→目标格，走棋！

---

## 实际体验如何

我用的 Qwen2.5 7B 模型（4bit 量化，在 CPU 上跑），每步 AI 大概需要 3-8 秒"思考"。

**人机对弈：**

1. **AI 有"性格"**：它不是追求最优解，而是追求"赢"——会走一些战术组合，有时候会贪吃弃子，偶尔还能走出漂亮的连将杀
2. **不需要 GPU**：CPU 就能跑，Qwen2.5 7B 4bit 在我的机器上大概占用 4GB 内存
3. **隐私安全**：一切在本地，不走任何云端 API
4. **免费**：不需要 OpenAI Key，不需要订阅

**AI vs AI（v1.5.0 新增）：**

最有意思的功能！让两个 LLM 下棋真的很欢乐——比如用 Qwen2.5 7B 对 DeepSeek-Coder 6.7B，看它们互相"算计"。

- **独立配置**：白方用 Qwen，黑方用 DeepSeek，温度也不一样
- **节奏可控**：可以慢放、暂停、一步步看
- **看 AI 思考**：AI Thinking 面板会显示每步的"内心独白"，比如"我将军了，对方必须挡"

**缺点（或者说是特点）：**

1. **AI 偶尔会犯蠢**：LLM 毕竟不是专用引擎，有时候会漏看战术，走出一些奇怪着法
2. **空响应**：偶尔 LLM 会返回空内容，代码里做了回退处理（自动选第一个合法着法，并在思考面板里标注 [fallback]）
3. **速度**：每步 3-8 秒，比 Stockfish 慢多了

但说实话，这些"缺点"反而让对弈更有趣——你不知道 AI 下一步会走什么，它有自己的"思路"（虽然有时候是错的）。

---

## 技术细节

### 架构

```
LLMChess/
├── main.py                    # GUI 入口
├── chess_app/
│   ├── __init__.py            # 包入口 + main()
│   ├── __main__.py            # python -m chess_app 支持
│   ├── board_widget.py        # PyQt6 棋盘渲染
│   ├── game_controller.py     # 主窗口 + AI vs AI 控制
│   ├── llm_connector.py       # OpenAI 兼容 API + 人设 + 思考解析
│   └── settings_dialog.py     # Tab 式设置（白/黑方独立配置）
├── build_deb.sh               # DEB 包构建脚本
└── .github/workflows/         # GitHub Actions 自动发布 PyPI
```

### LLM 交互方式

每步棋，程序会向 LLM 发送这样的提示（v1.5.0 新格式）：

```
You are a chess engine playing a chess game.

You will receive the current board state in FEN format
and a list of legal moves.

You are a calm, professional chess engine.

You must:
1. Briefly think about the position and the best move (1-3 sentences).
2. Then output your chosen move in UCI format (e.g. e2e4, g1f3, e7e8q).

Format your response as:
Reasoning: <your brief analysis>
Move: <UCI move>

Current board FEN: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR
Legal moves available: e2e4, e2e3, d2d4, ...
```

代码解析响应时会：
1. 先尝试匹配 `Reasoning: ... Move: xxx` 格式（拿到思考 + 着法）
2. 如果没找到，全局正则搜索 UCI 着法
3. 模糊匹配合法着法
4. 都失败就回退到第一个合法着法，思考里标 [fallback]

### 为什么用 UCI + FEN 而不是让 LLM 自己生成棋盘？

因为让 LLM 直接输出棋盘坐标太容易出错了。FEN + 合法着法列表给了 LLM 明确的约束，它只需要从列表中"选一个"，而不是"猜一个"，正确率大幅提升。

### AI vs AI 的实现

v1.5.0 的 AI vs AI 模式核心是**双 LLMConnector**：

```python
self._config_white = LLMConfig()  # 白方配置
self._config_black = LLMConfig()  # 黑方配置
self._connector_white = LLMConnector(self._config_white)
self._connector_black = LLMConnector(self._config_black)
```

每步根据当前轮到哪一方，调度对应的 connector：

```python
def _request_llm_move(self, color):
    connector = self._connector_white if color == chess.WHITE else self._connector_black
    # ... 在子线程调用 connector.get_move()
```

走棋完成后用 `QTimer.singleShot(delay, self._ai_vs_ai_step)` 调度下一步，`delay` 来自用户拖动的滑块。

### 技术栈

- **PyQt6**：跨平台 GUI，棋盘用 QPainter 手绘，支持高分辨率缩放
- **python-chess**：负责规则验证、FEN/PGN 转换、将军/将杀检测
- **httpx**：HTTP 客户端，兼容 OpenAI API 格式
- **QThread**：LLM 调用放在子线程，避免阻塞 UI
- **setuptools + Trusted Publisher**：GitHub Actions 自动发布 PyPI，零 Token 配置

---

## 开源地址

GitHub: https://github.com/oemoem12/LLMChess

PyPI: https://pypi.org/project/llmchess/

Release: https://github.com/oemoem12/LLMChess/releases

MIT 协议，随便用。

---

## 未来想法

- [x] 让 LLM 输出着法"理由"（**v1.5.0 已完成**：AI Thinking 面板）
- [x] AI vs AI 观战模式（**v1.5.0 已完成**）
- [ ] 保存 PGN 文件
- [ ] 赛后复盘（用 LLM 总结整局棋的关键转折点）
- [ ] Stockfish + LLM 混合模式（关键局面用引擎，常规局面用 LLM）
- [ ] 在线对战模式（两个用户各自连本地 LLM，通过房间匹配）

---

**总结一下**：LLM Chess 不是一个"最强"的象棋 AI，但它提供了一个有趣的视角——用对话式 AI 来下棋，体验上和传统引擎完全不同。如果你是 LLM 爱好者 + 象棋爱好者，不妨试试看。

v1.5.0 新增的 **AI vs AI 模式**尤其推荐——给两个不同的 LLM 装上不同的人设，让它们对弈，看着它们互相"算计"的感觉非常奇妙。

感兴趣的同学欢迎提 PR / 提 Issue。

---

**总结一下**：LLM Chess 不是一个"最强"的象棋 AI，但它提供了一个有趣的视角——用对话式 AI 来下棋，体验上和传统引擎完全不同。如果你是 LLM 爱好者 + 象棋爱好者，不妨试试看。

有什么想法欢迎在评论区交流。
