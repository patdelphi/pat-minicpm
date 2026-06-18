"""
程序说明：
本程序提供一个本地 Gradio WebUI，用于调用本地 OpenAI 兼容接口（/v1/chat/completions）。
支持：上传图片 + 输入文本 -> 发送到本地模型 -> 返回回答。
"""

from __future__ import annotations

import json
import mimetypes
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import gradio as gr
import requests

DEFAULT_SYSTEM_PROMPT = "请始终使用中文回答，不要输出思考过程，不要输出<think>标签中的内容，直接给出最终答案。"
MEDIA_FILE_LABEL = "媒体文件（支持图片/视频，音频暂不解析，可选）"
MEDIA_TEXT_PLACEHOLDER = "输入问题，支持图片或视频；纯音频当前仅返回提示…"
MEDIA_FILE_TYPES = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
]


@dataclass(frozen=True)
class AppConfig:
    model_id: str
    openai_base_url: str
    webui_host: str
    webui_port: int


def _load_env_file(env_file: str) -> None:
    if not os.path.exists(env_file):
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip().lstrip("\ufeff")
            v = v.strip()
            if k and k not in os.environ:
                os.environ[k] = v


def load_config() -> AppConfig:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _load_env_file(os.path.join(project_root, "config", "local.env"))

    model_id = os.environ.get("MODEL_ID", "openbmb/MiniCPM-V-4.6-Thinking-BNB")
    openai_base_url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
    webui_host = os.environ.get("WEBUI_HOST", "127.0.0.1")
    webui_port = int(os.environ.get("WEBUI_PORT", "7860"))

    return AppConfig(
        model_id=model_id,
        openai_base_url=openai_base_url,
        webui_host=webui_host,
        webui_port=webui_port,
    )


def _guess_mime_type(file_path: str) -> str:
    mt, _ = mimetypes.guess_type(file_path)
    return mt or "application/octet-stream"


def _file_to_input_url(file_path: str) -> str:
    """
    本地 WebUI 与本地 API 部署在同一台机器上时，优先传 file URL，
    避免把大视频整体转成 data URL 导致请求体过大。
    """
    return Path(file_path).resolve().as_uri()


def build_openai_payload(
    *,
    model_id: str,
    text: str,
    file_path: Optional[str],
    history: List[Union[Tuple[str, str], Dict[str, str]]],
) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": DEFAULT_SYSTEM_PROMPT,
        }
    ]

    for item in history:
        if isinstance(item, dict):
            role = str(item.get("role", "")).strip()
            content = str(item.get("content", ""))
            if role == "user":
                messages.append({"role": "user", "content": [{"type": "text", "text": content}]})
            elif role == "assistant":
                messages.append({"role": "assistant", "content": content})
            continue

        user_text, assistant_text = item
        messages.append({"role": "user", "content": [{"type": "text", "text": user_text}]})
        messages.append({"role": "assistant", "content": assistant_text})

    content: List[Dict[str, Any]] = []
    if file_path:
        mime_type = _guess_mime_type(file_path)
        input_url = _file_to_input_url(file_path)
        if mime_type.startswith("image/"):
            content.append({"type": "image_url", "image_url": {"url": input_url}})
        elif mime_type.startswith("video/"):
            content.append({"type": "video_url", "video_url": {"url": input_url}})
        elif mime_type.startswith("audio/"):
            content.append({"type": "audio_url", "audio_url": {"url": input_url}})
        else:
            raise ValueError(f"不支持的媒体类型：{mime_type}")
    if text.strip():
        content.append({"type": "text", "text": text.strip()})

    messages.append({"role": "user", "content": content})

    return {
        "model": model_id,
        "messages": messages,
        "stream": False,
    }


def call_openai_chat_completions(
    *,
    base_url: str,
    payload: Dict[str, Any],
    timeout_s: int = 300,
) -> str:
    url = f"{base_url}/chat/completions"
    try:
        resp = requests.post(url, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        return f"请求失败：{e}"
    except json.JSONDecodeError:
        return "响应解析失败：返回不是合法 JSON"

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return "响应格式不符合预期（缺少 choices[0].message.content）"


def append_chatbot_messages(
    history: List[Dict[str, str]],
    *,
    user_text: str,
    answer: str,
    file_path: Optional[str],
) -> List[Dict[str, str]]:
    # Gradio 6.x 的 Chatbot 默认使用 messages 格式，不能再返回 tuple 列表。
    display_text = user_text.strip()
    if not display_text and file_path:
        display_text = f"（已上传媒体：{os.path.basename(file_path)}）"
    if not display_text:
        display_text = "（已上传媒体）"
    return history + [
        {"role": "user", "content": display_text},
        {"role": "assistant", "content": answer},
    ]


def build_ui(cfg: AppConfig) -> gr.Blocks:
    with gr.Blocks(title="MiniCPM-V 4.6 本地 WebUI") as demo:
        gr.Markdown(
            f"当前模型：`{cfg.model_id}`  |  API：`{cfg.openai_base_url}`  |  时间：`{time.strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        gr.Markdown("支持上传图片或视频文件；纯音频文件当前仅返回占位提示。")
        chatbot = gr.Chatbot(height=520)
        state = gr.State([])

        with gr.Row():
            media = gr.File(type="filepath", label=MEDIA_FILE_LABEL, file_types=MEDIA_FILE_TYPES)
            text = gr.Textbox(lines=4, label="输入", placeholder=MEDIA_TEXT_PLACEHOLDER)

        with gr.Row():
            send = gr.Button("发送", variant="primary")
            clear = gr.Button("清空")

        def _on_send(file_path: Optional[str], user_text: str, history: List[Dict[str, str]]):
            history = history or []
            if not (file_path or user_text.strip()):
                return history, history

            try:
                payload = build_openai_payload(
                    model_id=cfg.model_id,
                    text=user_text,
                    file_path=file_path,
                    history=history,
                )
                answer = call_openai_chat_completions(base_url=cfg.openai_base_url, payload=payload)
            except ValueError as e:
                answer = str(e)
            new_history = append_chatbot_messages(history, user_text=user_text, answer=answer, file_path=file_path)
            return new_history, new_history

        def _on_clear():
            return [], []

        send.click(_on_send, inputs=[media, text, state], outputs=[chatbot, state])
        clear.click(_on_clear, inputs=[], outputs=[chatbot, state])

    return demo


def main() -> None:
    cfg = load_config()
    app = build_ui(cfg)
    app.launch(server_name=cfg.webui_host, server_port=cfg.webui_port)


if __name__ == "__main__":
    main()
