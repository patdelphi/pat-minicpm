"""
程序说明：
本地 OpenAI 兼容 API：
- GET  /health
- GET  /v1/models
- POST /v1/chat/completions
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from api.model_runtime import ModelRuntime
from api.openai_compat import (
    AudioInputNotSupportedError,
    ensure_default_system_message,
    parse_openai_messages,
    strip_think_content,
)
from api.settings import load_settings


app = FastAPI()
settings = load_settings()
runtime = ModelRuntime(model_dir=settings.model_dir, quant_dir=settings.quant_dir)


class ImageUrl(BaseModel):
    url: str


class ContentPart(BaseModel):
    type: str
    text: Optional[str] = None
    image_url: Optional[ImageUrl] = None


class ChatMessage(BaseModel):
    role: str
    content: Any


class ChatCompletionsRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    max_tokens: Optional[int] = None


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> Dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": "MiniCPM-V-4.6-Thinking-int4" if settings.quant_dir else "MiniCPM-V-4.6-Thinking",
                "object": "model",
            }
        ],
    }


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionsRequest) -> Dict[str, Any]:
    if req.stream:
        raise HTTPException(status_code=400, detail="当前仅支持 stream=false")

    try:
        request_messages = ensure_default_system_message([m.model_dump() for m in req.messages])
        parsed_messages, _ = parse_openai_messages(request_messages)
        max_new_tokens = int(req.max_tokens or settings.max_new_tokens)
        content = strip_think_content(runtime.infer(parsed_messages, max_new_tokens=max_new_tokens))
    except AudioInputNotSupportedError as e:
        content = str(e)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败：{e}")

    now = int(time.time())
    return {
        "id": f"chatcmpl-{now}",
        "object": "chat.completion",
        "created": now,
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }
