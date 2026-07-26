import re
import json
import httpx
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    provider: str = "ollama"
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen2.5:7b"
    api_key: str = ""
    temperature: float = 0.3
    max_tokens: int = 512
    timeout: float = 60.0
    # 自定义 AI 思考风格（可选）。不同的"角色"会有不同的语气/策略。
    persona: str = ""


# 不同的 AI 人设：影响思考展示风格
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


@dataclass
class LLMResponse:
    """LLM 的完整响应：包含思考过程和最终着法"""
    move: Optional[str]  # UCI 着法
    reasoning: str       # AI 的思考/解释
    raw: str             # 原始返回内容
    used_fallback: bool = False  # 是否使用了回退（无着法时取第一个合法着法）


class LLMConnector:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.config.timeout)
        return self._client

    def _get_persona(self) -> str:
        if self.config.persona and self.config.persona in PERSONAS:
            return PERSONAS[self.config.persona]
        if self.config.persona:
            # 自定义人设
            return f"You are a chess player with this style: {self.config.persona}"
        return PERSONAS["default"]

    def _build_prompt(self, fen: str, legal_moves: list[str]) -> str:
        moves_str = ", ".join(legal_moves)
        persona = self._get_persona()
        return SYSTEM_PROMPT.format(
            fen=fen,
            legal_moves=moves_str,
            persona=persona,
        )

    def _get_chat_endpoint(self) -> str:
        base = self.config.base_url.rstrip("/")
        if self.config.provider == "ollama" and "/v1" not in base:
            base += "/v1"
        return f"{base}/chat/completions"

    def _build_request_body(self, fen: str, legal_moves: list[str]) -> dict:
        prompt = self._build_prompt(fen, legal_moves)
        return {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": False,
        }

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

        # 2. 如果没找到 Move: 前缀，用 UCI 正则全局搜索
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

        # 4. 如果仍然没有 reasoning，但内容比较长，就把前半部分当 reasoning
        if not reasoning and len(content) > 30:
            # 去掉 Move 行后剩下的内容
            cleaned = re.sub(
                r'(?:^|\n)\s*(?:Move|Answer|My move|My answer)\s*[:：].*$',
                '', content, flags=re.IGNORECASE,
            ).strip()
            # 去掉开头的 "Reasoning: ..."
            cleaned = re.sub(
                r'^\s*(?:Reasoning|Analysis|Think|Thought)\s*[:：]\s*',
                '', cleaned, flags=re.IGNORECASE,
            ).strip()
            reasoning = cleaned[:500]

        return move, reasoning

    def get_move(
        self, fen: str, legal_moves: list[str]
    ) -> LLMResponse:
        """请求 LLM 下一步棋，返回完整响应（包含思考）"""
        body = self._build_request_body(fen, legal_moves)
        endpoint = self._get_chat_endpoint()

        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        try:
            response = self.client.post(
                endpoint, json=body, headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ConnectionError(f"LLM request failed: {e}")

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError):
            raise ValueError(
                f"Unexpected API response format: {json.dumps(data, indent=2)[:500]}"
            )

        move, reasoning = self._parse_response(content, legal_moves)
        used_fallback = False

        if not move:
            if legal_moves:
                move = legal_moves[0]
                used_fallback = True
                reasoning = (
                    reasoning or f"[LLM 返回无效，已回退到第一个合法着法 {move}]"
                )
            else:
                raise ValueError("No legal moves available")

        return LLMResponse(
            move=move,
            reasoning=reasoning,
            raw=content,
            used_fallback=used_fallback,
        )

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
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

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

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
