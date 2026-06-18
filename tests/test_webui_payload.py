"""
程序说明：
WebUI 的最小单元测试：校验 OpenAI 请求体构造与 Gradio 消息格式兼容性。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from webui.gradio_app import (
    MEDIA_FILE_LABEL,
    MEDIA_FILE_TYPES,
    MEDIA_TEXT_PLACEHOLDER,
    append_chatbot_messages,
    build_openai_payload,
)


def test_build_openai_payload_with_image_and_text(tmp_path):
    img = tmp_path / "a.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 32)

    payload = build_openai_payload(
        model_id="openbmb/MiniCPM-V-4.6-Thinking-BNB",
        text="hello",
        file_path=str(img),
        history=[("q1", "a1")],
    )

    assert payload["model"] == "openbmb/MiniCPM-V-4.6-Thinking-BNB"
    assert payload["stream"] is False
    assert payload["messages"][0]["role"] == "system"
    assert "中文回答" in payload["messages"][0]["content"]
    assert payload["messages"][1]["role"] == "user"
    assert payload["messages"][2]["role"] == "assistant"

    last = payload["messages"][-1]
    assert last["role"] == "user"
    assert isinstance(last["content"], list)

    image_part = last["content"][0]
    assert image_part["type"] == "image_url"
    url = image_part["image_url"]["url"]
    assert url.startswith("file:///")

    text_part = last["content"][-1]
    assert text_part["type"] == "text"
    assert text_part["text"] == "hello"


def test_build_openai_payload_with_video_file(tmp_path):
    video = tmp_path / "a.mp4"
    video.write_bytes(b"fake-video")

    payload = build_openai_payload(
        model_id="MiniCPM-V-4.6-Thinking-int4",
        text="分析视频",
        file_path=str(video),
        history=[],
    )

    last = payload["messages"][-1]
    assert last["content"][0]["type"] == "video_url"
    assert last["content"][0]["video_url"]["url"].startswith("file:///")
    assert last["content"][-1]["text"] == "分析视频"


def test_build_openai_payload_with_audio_file(tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"fake-audio")

    payload = build_openai_payload(
        model_id="MiniCPM-V-4.6-Thinking-int4",
        text="分析音频",
        file_path=str(audio),
        history=[],
    )

    last = payload["messages"][-1]
    assert last["content"][0]["type"] == "audio_url"
    assert last["content"][0]["audio_url"]["url"].startswith("file:///")
    assert last["content"][-1]["text"] == "分析音频"


def test_build_openai_payload_with_gradio_messages_history():
    payload = build_openai_payload(
        model_id="MiniCPM-V-4.6-Thinking-int4",
        text="继续",
        file_path=None,
        history=[
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我在。"},
        ],
    )

    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert payload["messages"][1]["content"][0]["text"] == "你好"
    assert payload["messages"][2]["role"] == "assistant"
    assert payload["messages"][2]["content"] == "你好，我在。"
    assert payload["messages"][-1]["content"][-1]["text"] == "继续"


def test_append_chatbot_messages_uses_messages_format():
    out = append_chatbot_messages([], user_text="", answer="已收到图片", file_path=None)
    assert out == [
        {"role": "user", "content": "（已上传媒体）"},
        {"role": "assistant", "content": "已收到图片"},
    ]


def test_webui_media_copy_mentions_video_support():
    assert "视频" in MEDIA_FILE_LABEL
    assert "视频" in MEDIA_TEXT_PLACEHOLDER
    assert ".mp4" in MEDIA_FILE_TYPES
