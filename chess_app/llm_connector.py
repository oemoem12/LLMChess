"""
LLM Connector - 连接本地/云端 LLM 服务
支持 Ollama / llama.cpp / LM Studio / OpenAI / DeepSeek / 自定义 OpenAI 兼容 API
"""

import re
import json
import time
import httpx
from dataclasses import dataclass, field
from typing import Optional


# ============================================================================
# 配置
# ============================================================================

@dataclass
class LLMConfig:
    provider: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen2.5:7b"
    api_key: str = ""
    temperature: float = 0.3
    max_tokens: int = 512
    timeout: float = 60.0
    persona: str = ""
    # 云端 API 专用
    org_id: str = ""          # OpenAI 组织 ID（可选）
    project_id: str = ""      # OpenAI 项目 ID（可选）


# ============================================================================
# 预设配置
# ============================================================================

PRESET_CONFIGS = {
    "ollama": {
        "provider": "ollama",
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b",
    },
    "llamacpp": {
        "provider": "llamacpp",
        "base_url": "http://localhost:8080/v1",
        "model": "llama",
    },
    "lmstudio": {
        "provider": "lmstudio",
        "base_url": "http://localhost:1234/v1",
        "model": "local-model",
    },
    "openai": {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "deepseek": {
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
}


# ============================================================================
# AI 人设
# ============================================================================

PERSONAS = {
    "default": "You are a calm, professional chess engine.",
    "aggressive": "You are an aggressive chess player who loves attacks and sacrifices.",
    "defensive": "You are a defensive chess player who values king safety and solid positions.",
    "creative": "You are a creative chess player who likes unusual openings and tactical surprises.",
    "teacher": "You are a chess teacher who explains your reasoning clearly.",
}


SYSTEM_PROMPT = """You are a chess engine playing a chess game.

You will receive the current board state in FEN (Forsyth-Edwards Notation) format
and a list of legal moves.

{persona}

You must:
1. Briefly think about the position and the best move (1-3 sentences).
2. Then output your chosen move in UCI format (e.g. e2e4, g1f3, e7e8q).

Format your response as:
Reasoning: <your brief analysis>
Move: <UCI move>

The move MUST be in the legal moves list.
For pawn promotion, append the piece letter: q=queen, r=rook, b=bishop, n=knight.

Current board FEN: {fen}
Legal moves available: {legal_moves}
"""


# ============================================================================
# 响应
# ============================================================================

@dataclass
class LLMResponse:
    """LLM 的完整响应：包含思考过程和最终着法"""
    move: Optional[str]
    reasoning: str
    raw: str
    used_fallback: bool = False
    side: str = ""  # "white" / "black"


# ============================================================================
# Connector
# ============================================================================

class LLMConnector:
    """
    连接 LLM 服务。每个实例拥有独立的 httpx.Client，
    确保 AI vs AI 模式下两个 connector 互不干扰。
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client: Optional[httpx.Client] = None
        self._request_counter = 0  # 用于调试/日志

    @property
    def client(self) -> httpx.Client:
        """懒加载，每个 connector 实例独立创建"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.config.timeout,
                # 关键修复：禁用连接池复用，防止 AI vs AI 同模型时串扰
                limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
            )
        return self._client

    # ------------------------------------------------------------------
    # 端点
    # ------------------------------------------------------------------

    def _get_chat_endpoint(self) -> str:
        base = self.config.base_url.rstrip("/")
        provider = self.config.provider
        if provider == "ollama" and "/v1" not in base:
            base += "/v1"
        return f"{base}/chat/completions"

    # ------------------------------------------------------------------
    # 请求头
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        key = self.config.api_key
        provider = self.config.provider

        if key:
            if provider in ("openai", "deepseek"):
                headers["Authorization"] = f"Bearer {key}"
            else:
                headers["Authorization"] = f"Bearer {key}"

        # OpenAI 可选 org/project
        if provider == "openai":
            if self.config.org_id:
                headers["OpenAI-Organization"] = self.config.org_id
            if self.config.project_id:
                headers["OpenAI-Project"] = self.config.project_id

        return headers

    # ------------------------------------------------------------------
    # 提示词
    # ------------------------------------------------------------------

    def _get_persona(self) -> str:
        if self.config.persona and self.config.persona in PERSONAS:
            return PERSONAS[self.config.persona]
        if self.config.persona:
            return f"You are a chess player with this style: {self.config.persona}"
        return PERSONAS["default"]

    def _build_prompt(self, fen: str, legal_moves: list[str]) -> str:
        return SYSTEM_PROMPT.format(
            fen=fen,
            legal_moves=", ".join(legal_moves),
            persona=self._get_persona(),
        )

    def _build_request_body(self, fen: str, legal_moves: list[str]) -> dict:
        return {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": self._build_prompt(fen, legal_moves)}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }

    # ------------------------------------------------------------------
    # 响应解析
    # ------------------------------------------------------------------

    def _parse_response(
        self, content: str, legal_moves: list[str]
    ) -> tuple[Optional[str], str]:
        """从 LLM 响应中提取 (UCI 着法, 思考过程)"""
        content = content.strip()
        reasoning = ""
        move = None

        # 1. 尝试解析 "Reasoning: ... Move: xxx" 格式
        m_reason = re.search(
            r'(?:Reasoning|Analysis|Think|Thought)\s*[:：]\s*(.+?)(?:\n|$)',
            content, re.IGNORECASE | re.DOTALL,
        )
        m_move = re.search(
            r'(?:^|\n)\s*(?:Move|Answer|My move|My answer)\s*[:：]\s*([a-h][1-8][a-h][1-8][qrbn]?)',
            content, re.IGNORECASE,
        )

        if m_reason:
            reasoning = m_reason.group(1).strip()[:500]
        if m_move:
            candidate = m_move.group(1).lower()
            if candidate in legal_moves:
                move = candidate

        # 2. 全局 UCI 正则搜索
        if move is None:
            uci_pattern = re.compile(
                r'\b([a-h][1-8][a-h][1-8][qrbn]?)\b', re.IGNORECASE
            )
            for m in uci_pattern.findall(content):
                cand = m.lower()
                if cand in legal_moves:
                    move = cand
                    break

        # 3. 模糊匹配
        if move is None:
            content_lower = content.lower()
            for m in legal_moves:
                if m in content_lower:
                    move = m
                    break

        # 4. 提取剩余内容为 reasoning
        if not reasoning and len(content) > 30:
            cleaned = re.sub(
                r'(?:^|\n)\s*(?:Move|Answer|My move|My answer)\s*[:：].*$',
                '', content, flags=re.IGNORECASE,
            ).strip()
            cleaned = re.sub(
                r'^\s*(?:Reasoning|Analysis|Think|Thought)\s*[:：]\s*',
                '', cleaned, flags=re.IGNORECASE,
            ).strip()
            reasoning = cleaned[:500]

        return move, reasoning

    # ------------------------------------------------------------------
    # 核心：获取着法
    # ------------------------------------------------------------------

    def get_move(
        self, fen: str, legal_moves: list[str], side: str = ""
    ) -> LLMResponse:
        """
        请求 LLM 下一步棋。
        side: "white" / "black" — 用于日志和调试，区分 AI vs AI 的两个请求
        """
        self._request_counter += 1
        req_id = self._request_counter

        body = self._build_request_body(fen, legal_moves)
        endpoint = self._get_chat_endpoint()
        headers = self._build_headers()

        try:
            response = self.client.post(
                endpoint, json=body, headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ConnectionError(f"LLM request failed (req#{req_id}, side={side}): {e}")

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError):
            raise ValueError(
                f"Unexpected API response (req#{req_id}): {json.dumps(data, indent=2)[:500]}"
            )

        move, reasoning = self._parse_response(content, legal_moves)
        used_fallback = False

        if not move:
            if legal_moves:
                move = legal_moves[0]
                used_fallback = True
                reasoning = (
                    reasoning or f"[LLM returned invalid, fell back to first legal move {move}]"
                )
            else:
                raise ValueError("No legal moves available")

        return LLMResponse(
            move=move,
            reasoning=reasoning,
            raw=content,
            used_fallback=used_fallback,
            side=side,
        )

    # ------------------------------------------------------------------
    # 连接测试
    # ------------------------------------------------------------------

    def test_connection(self) -> tuple[bool, str]:
        endpoint = self._get_chat_endpoint()
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": "Reply with only the word: OK"}
            ],
            "temperature": 0,
            "max_tokens": 16,
        }
        headers = self._build_headers()

        try:
            response = self.client.post(
                endpoint, json=body, headers=headers, timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return True, f"Connected! Model: {self.config.model}. Response: {content[:100]}"
        except httpx.ConnectError:
            return False, f"Cannot connect to {endpoint}. Is the server running?"
        except httpx.HTTPStatusError as e:
            return False, f"HTTP error {e.response.status_code}: {e.response.text[:300]}"
        except Exception as e:
            return False, f"Connection test failed: {e}"

    # ------------------------------------------------------------------
    # 清理
    # ------------------------------------------------------------------

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
