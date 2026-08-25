from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import win32crypt


APP_NAME = "PaperTranslator"


@dataclass(frozen=True)
class AppConfig:
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4.1-mini"
    target_language: str = "简体中文"
    timeout_seconds: int = 60
    port: int = 8765

    def validate(self) -> None:
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("API 地址必须以 http:// 或 https:// 开头")
        if not self.model.strip():
            raise ValueError("模型名称不能为空")
        if not self.target_language.strip():
            raise ValueError("目标语言不能为空")
        if not 1 <= self.timeout_seconds <= 300:
            raise ValueError("超时时间必须在 1 到 300 秒之间")
        if not 1024 <= self.port <= 65535:
            raise ValueError("本地端口必须在 1024 到 65535 之间")


class ConfigStore:
    """Persists one validated configuration and hides secret protection details."""

    def __init__(self, path: Path | None = None) -> None:
        appdata = Path(os.environ.get("APPDATA", Path.home()))
        self.path = path or appdata / APP_NAME / "config.json"

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            encrypted_key = payload.pop("api_key_encrypted", "")
            payload.pop("api_key", None)
            config = AppConfig(api_key=self._unprotect(encrypted_key), **payload)
            config.validate()
            return config
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        config.validate()
        payload = asdict(config)
        api_key = payload.pop("api_key")
        payload["api_key_encrypted"] = self._protect(api_key)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)

    @staticmethod
    def _protect(value: str) -> str:
        if not value:
            return ""
        encrypted = win32crypt.CryptProtectData(
            value.encode("utf-8"), APP_NAME, None, None, None, 0
        )
        return base64.b64encode(encrypted).decode("ascii")

    @staticmethod
    def _unprotect(value: str) -> str:
        if not value:
            return ""
        encrypted = base64.b64decode(value)
        _, clear = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        return clear.decode("utf-8")

