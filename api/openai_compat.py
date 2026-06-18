"""
程序说明：
将 OpenAI Chat Completions 请求格式转换为 MiniCPM-V 4.6 的 messages 格式，并做图片解码。
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from aipython import media_inputs

DEFAULT_SYSTEM_PROMPT = "请始终使用中文回答，不要输出思考过程，不要输出<think>标签中的内容，直接给出最终答案。"
AUDIO_INPUT_NOT_SUPPORTED_MESSAGE = "当前部署的 MiniCPM-V 4.6 仅支持图片和视频解析，暂不支持纯音频解析。"


@dataclass(frozen=True)
class ParsedUserContent:
    text: str
    images: List[Image.Image]


class AudioInputNotSupportedError(ValueError):
    """
    显式音频输入的占位错误。
    API 层会将该错误转成友好的助手回复，而不是 400。
    """


def strip_think_content(text: str) -> str:
    """
    过滤模型输出中的思考过程，只保留最终可展示给用户的答案。
    """
    without_think = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    if re.search(r"</think>", without_think, flags=re.IGNORECASE):
        # 有些 Thinking 模型会丢失开标签，只剩结束标签；这种情况下保留最后一个结束标签后的内容。
        without_think = re.split(r"</think>", without_think, flags=re.IGNORECASE)[-1]
    without_think = re.sub(r"</?think>", "", without_think, flags=re.IGNORECASE)
    return without_think.strip()


def ensure_default_system_message(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    如果调用方没有提供 system 提示，则注入默认提示，统一输出中文且尽量只返回最终答案。
    """
    if any(m.get("role") == "system" for m in messages):
        return messages
    return [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}, *messages]


def parse_openai_messages(messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    返回：
    - transformers 侧 messages（role/content，content 里含 PIL.Image 与 text）
    - 最后一条用户消息文本（用于日志/trace，可为 None）
    """

    out: List[Dict[str, Any]] = []
    last_user_text: Optional[str] = None

    for m in messages:
        role = m.get("role")
        content = m.get("content")

        if role not in ("system", "user", "assistant"):
            raise ValueError(f"不支持的 role：{role}")

        if role in ("system", "assistant"):
            if isinstance(content, str):
                out.append({"role": role, "content": [{"type": "text", "text": content}]})
                continue
            raise ValueError(f"{role} 仅支持 string content")

        if role == "user":
            texts: List[str] = []
            mm_content: List[Dict[str, Any]] = []

            if isinstance(content, str):
                text_value = content.strip()
                if text_value:
                    texts.append(text_value)
                    mm_content.append({"type": "text", "text": text_value})
            elif isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    ptype = part.get("type")
                    if ptype == "text":
                        t = (part.get("text") or "").strip()
                        if t:
                            texts.append(t)
                            mm_content.append({"type": "text", "text": t})
                    elif ptype == "image_url":
                        url = ((part.get("image_url") or {}).get("url") or "").strip()
                        if not url:
                            continue
                        mm_content.append({"type": "image", "image": media_inputs.load_image_input(url)})
                    elif ptype == "video_url":
                        url = ((part.get("video_url") or {}).get("url") or "").strip()
                        if not url:
                            continue
                        for frame in media_inputs.extract_video_frames(url):
                            mm_content.append({"type": "image", "image": frame})
                    elif ptype == "audio_url":
                        raise AudioInputNotSupportedError(AUDIO_INPUT_NOT_SUPPORTED_MESSAGE)
                    else:
                        raise ValueError(f"不支持的 user content.type：{ptype}")
            else:
                raise ValueError("user.content 必须是 string 或 list")

            text = "\n".join(texts).strip()
            last_user_text = text or last_user_text

            out.append({"role": "user", "content": mm_content})

    return out, last_user_text
