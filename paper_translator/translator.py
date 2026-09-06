from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .config import AppConfig
from .formulas import split_formulas


MAX_TEXT_LENGTH = 20_000


class TranslationError(RuntimeError):
    pass


@dataclass(frozen=True)
class TranslationResult:
    source: str
    translation: str
    model: str


class Translator:
    """Deep module: one translate interface hides prompting and wire formats."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def translate(self, text: str) -> TranslationResult:
        source = normalize_selection(text)
        if not source:
            raise TranslationError("没有获取到选中的文字")
        if len(source) > MAX_TEXT_LENGTH:
            raise TranslationError(f"选中文字过长，最多支持 {MAX_TEXT_LENGTH} 个字符")
        if not self.config.api_key and not _is_local_url(self.config.base_url):
            raise TranslationError("请先在设置中填写 API Key")

        request = urllib.request.Request(
            chat_completions_url(self.config.base_url),
            data=json.dumps(self._payload(source), ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                **(
                    {"Authorization": f"Bearer {self.config.api_key}"}
                    if self.config.api_key
                    else {}
                ),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise TranslationError(f"LLM 接口返回 {exc.code}：{_error_detail(detail)}") from exc
        except urllib.error.URLError as exc:
            raise TranslationError(f"无法连接 LLM 接口：{exc.reason}") from exc
        except (TimeoutError, json.JSONDecodeError) as exc:
            raise TranslationError("LLM 接口超时或返回了无效 JSON") from exc

        translation = extract_chat_content(body)
        return TranslationResult(source, translation.strip(), self.config.model)

    def _payload(self, source: str) -> dict[str, Any]:
        return {
            "model": self.config.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是严谨的学术翻译助手。保持术语、缩写、公式、引用编号和专有名词准确；"
                        f"把用户文本翻译成{self.config.target_language}。"
                        r"保留已有 LaTeX 公式的命令、变量、上下标和环境，不翻译公式内部内容。"
                        r"数学表达式使用 LaTeX，行内公式用 \( ... \)，独立公式用 \[ ... \]。"
                        "不要用代码块包裹译文或公式，不要猜测或补写原文缺失的公式。"
                        "只输出译文，不要解释，不要加标题。"
                    ),
                },
                {"role": "user", "content": source},
            ],
        }


def normalize_selection(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    parts = []
    for segment in split_formulas(text):
        value = segment.raw
        if not segment.protected:
            value = re.sub(r"(?<=\w)-\n(?=\w)", "", value)
            value = re.sub(r"(?<!\n)\n(?!\n)", " ", value)
            value = re.sub(r"[ \t]+", " ", value)
        parts.append(value)
    return "".join(parts)


def chat_completions_url(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    return f"{url}/chat/completions"


def extract_chat_content(payload: dict[str, Any]) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise TranslationError("LLM 返回中缺少 choices[0].message.content") from exc
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        joined = "".join(parts).strip()
        if joined:
            return joined
    raise TranslationError("LLM 返回了空译文")


def _is_local_url(url: str) -> bool:
    return url.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]"))


def _error_detail(raw: str) -> str:
    try:
        payload = json.loads(raw)
        return str(payload.get("error", {}).get("message") or raw)
    except (json.JSONDecodeError, AttributeError):
        return raw or "未知错误"
