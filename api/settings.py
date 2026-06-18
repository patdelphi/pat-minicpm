"""
程序说明：
读取本地运行配置（从环境变量或 "config/local.env" 注入的 Env 读取）。
"""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    model_dir: str
    quant_dir: str
    host: str
    port: int
    max_new_tokens: int


def load_settings() -> Settings:
    model_dir = os.environ.get("MODEL_DIR", os.path.join("models", "MiniCPM-V-4.6-Thinking"))
    quant_dir = os.environ.get("QUANT_DIR", os.path.join("models", "MiniCPM-V-4.6-Thinking-int4"))
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", "8000"))
    max_new_tokens = int(os.environ.get("MAX_NEW_TOKENS", "1024"))

    return Settings(
        model_dir=model_dir,
        quant_dir=quant_dir,
        host=host,
        port=port,
        max_new_tokens=max_new_tokens,
    )
