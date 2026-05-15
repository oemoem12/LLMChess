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


SYSTEM_PROMPT = """You are a chess engine. You play chess against a human user.

You will receive the current board state in FEN (Forsyth-Edwards Notation) format and a list of legal moves.
You MUST choose ONE move from the provided legal moves list and respond with ONLY that move in UCI format.

Rules:
1. Respond with ONLY the UCI move string, NO extra text.
2. The move MUST be in the legal moves list.
3. Play strong, tactical chess - aim to checkmate or win material.
4. If in check, choose a move that gets out of check.
5. For pawn promotion, append the piece letter: q=queen, r=rook, b=bishop, n=knight.

Current board FEN: {fen}
Legal moves available (choose one): {legal_moves}

Your move (ONLY the UCI string, no other text):"""


class LLMConnector:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.config.timeout)
        return self._client

    def _build_prompt(self, fen: str, legal_moves: list[str]) -> str:
        moves_str = ", ".join(legal_moves)
        return SYSTEM_PROMPT.format(fen=fen, legal_moves=moves_str)

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

    def _parse_response(self, content: str, legal_moves: list[str]) -> Optional[str]:
        content = content.strip()

        uci_pattern = re.compile(r'\b([a-h][1-8][a-h][1-8][qrbn]?)\b', re.IGNORECASE)
        matches = uci_pattern.findall(content)

        for match in matches:
            move_lower = match.lower()
            if move_lower in legal_moves:
                return move_lower

        for move in legal_moves:
            if move in content.lower():
                return move

        first_line = content.split('\n')[0].strip().lower()
        if first_line in legal_moves:
            return first_line

        for move in legal_moves:
            pattern = re.escape(move)
            if re.search(pattern, content, re.IGNORECASE):
                return move

        return None

    def get_move(self, fen: str, legal_moves: list[str]) -> Optional[str]:
        body = self._build_request_body(fen, legal_moves)
        endpoint = self._get_chat_endpoint()

        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        try:
            response = self.client.post(
                endpoint,
                json=body,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ConnectionError(f"LLM request failed: {e}")

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ValueError(f"Unexpected API response format: {json.dumps(data, indent=2)[:500]}")

        if not content:
            first_legal = legal_moves[0] if legal_moves else None
            if first_legal:
                print(f"[WARNING] LLM returned empty response. Falling back to {first_legal}")
                return first_legal
            raise ValueError("LLM returned empty response and no legal moves available")

        move = self._parse_response(content, legal_moves)
        if move is None:
            first_legal = legal_moves[0] if legal_moves else None
            if first_legal:
                print(f"[WARNING] LLM returned invalid move: '{content[:200]}'. Falling back to {first_legal}")
                return first_legal
            raise ValueError(f"LLM returned unparseable move: '{content[:200]}' and no legal moves available")

        return move

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
                endpoint,
                json=body,
                headers=headers,
                timeout=15.0,
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