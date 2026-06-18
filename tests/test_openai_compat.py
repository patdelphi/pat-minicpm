"""
程序说明：
测试 OpenAI 请求格式解析与思考过程过滤（仅解析，不触发模型推理）。
"""

import base64
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.openai_compat import (
    AUDIO_INPUT_NOT_SUPPORTED_MESSAGE,
    AudioInputNotSupportedError,
    DEFAULT_SYSTEM_PROMPT,
    ensure_default_system_message,
    parse_openai_messages,
    strip_think_content,
)


def test_parse_openai_messages_with_data_url():
    img = Image.new("RGB", (2, 2), (255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    data_url = f"data:image/png;base64,{b64}"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": "hello"},
            ],
        }
    ]

    out, last_text = parse_openai_messages(messages)
    assert last_text == "hello"
    assert out[0]["role"] == "user"
    assert out[0]["content"][-1]["type"] == "text"
    assert out[0]["content"][-1]["text"] == "hello"


def test_parse_openai_messages_with_video_url_uses_extracted_frames(monkeypatch, tmp_path):
    video_file = tmp_path / "demo.mp4"
    video_file.write_bytes(b"fake-video")

    extracted_frames = [
        Image.new("RGB", (4, 4), (255, 0, 0)),
        Image.new("RGB", (4, 4), (0, 255, 0)),
    ]

    from api import openai_compat

    monkeypatch.setattr(openai_compat.media_inputs, "extract_video_frames", lambda _url: extracted_frames)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "video_url", "video_url": {"url": video_file.as_uri()}},
                {"type": "text", "text": "describe video"},
            ],
        }
    ]

    out, last_text = parse_openai_messages(messages)
    assert last_text == "describe video"
    assert out[0]["role"] == "user"
    assert out[0]["content"][0]["type"] == "image"
    assert out[0]["content"][1]["type"] == "image"
    assert out[0]["content"][-1]["type"] == "text"
    assert out[0]["content"][-1]["text"] == "describe video"


def test_parse_openai_messages_raises_placeholder_for_audio_input():
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "audio_url", "audio_url": {"url": "file:///tmp/demo.wav"}},
                {"type": "text", "text": "summarize"},
            ],
        }
    ]

    with pytest.raises(AudioInputNotSupportedError) as exc_info:
        parse_openai_messages(messages)

    assert str(exc_info.value) == AUDIO_INPUT_NOT_SUPPORTED_MESSAGE


def test_strip_think_content_removes_think_block():
    text = "<think>内部推理</think>\n最终答案"
    assert strip_think_content(text) == "最终答案"


def test_strip_think_content_keeps_plain_text():
    text = "直接答案"
    assert strip_think_content(text) == "直接答案"


def test_strip_think_content_handles_orphan_closing_tag():
    text = "推理过程一\n推理过程二\n</think>\n最终答案"
    assert strip_think_content(text) == "最终答案"


def test_ensure_default_system_message_adds_default_prompt():
    messages = [{"role": "user", "content": "你好"}]
    out = ensure_default_system_message(messages)
    assert out[0]["role"] == "system"
    assert out[0]["content"] == DEFAULT_SYSTEM_PROMPT
    assert out[1]["role"] == "user"


def test_ensure_default_system_message_preserves_existing_system():
    messages = [
        {"role": "system", "content": "自定义系统提示"},
        {"role": "user", "content": "你好"},
    ]
    out = ensure_default_system_message(messages)
    assert out == messages
