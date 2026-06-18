"""
程序说明：
测试统一启动器的端口顺延规则，确保 API / WebUI 会自动选择可用端口，
并正确生成 WebUI 要使用的 OpenAI Base URL。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aipython.launch_ports import build_launch_plan, choose_available_port


def test_choose_available_port_skips_occupied_ports():
    occupied_ports = {8000, 8001, 7860}

    def fake_is_available(port: int) -> bool:
        return port not in occupied_ports

    assert choose_available_port(8000, is_port_available=fake_is_available) == 8002
    assert choose_available_port(7860, is_port_available=fake_is_available) == 7861


def test_build_launch_plan_uses_selected_ports_and_local_api_url():
    occupied_ports = {8000, 7860, 7861}

    def fake_is_available(port: int) -> bool:
        return port not in occupied_ports

    plan = build_launch_plan(
        api_host="0.0.0.0",
        api_port=8000,
        webui_host="127.0.0.1",
        webui_port=7860,
        is_port_available=fake_is_available,
    )

    assert plan["api_port"] == 8001
    assert plan["webui_port"] == 7862
    assert plan["openai_base_url"] == "http://127.0.0.1:8001/v1"


def test_build_launch_plan_preserves_non_wildcard_host_in_api_url():
    plan = build_launch_plan(
        api_host="192.168.1.20",
        api_port=8000,
        webui_host="127.0.0.1",
        webui_port=7860,
        is_port_available=lambda _port: True,
    )

    assert plan["api_port"] == 8000
    assert plan["webui_port"] == 7860
    assert plan["openai_base_url"] == "http://192.168.1.20:8000/v1"
