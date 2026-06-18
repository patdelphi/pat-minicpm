"""
程序说明：
为本地启动脚本提供端口顺延与启动配置生成能力，
用于自动选择可用的 API / WebUI 端口，并生成对应的 OpenAI Base URL。
"""

from __future__ import annotations

import json
import os
import socket
from typing import Callable, Dict

DEFAULT_API_PATH = "/v1"
WILDCARD_HOSTS = {"0.0.0.0", "::", ""}


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """
    检查目标端口是否可绑定。
    使用 bind 判断可用性，避免依赖平台命令输出格式。
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def choose_available_port(
    start_port: int,
    *,
    is_port_available: Callable[[int], bool] | None = None,
    max_attempts: int = 100,
) -> int:
    """
    从给定起始端口开始，顺延查找首个可用端口。
    """
    checker = is_port_available or (lambda port: is_port_available_on_localhost(port))
    for offset in range(max_attempts):
        candidate = start_port + offset
        if checker(candidate):
            return candidate
    raise RuntimeError(f"No available port found from {start_port} within {max_attempts} attempts.")


def is_port_available_on_localhost(port: int) -> bool:
    """
    统一对 localhost 做检查，便于测试中替换实现。
    """
    return is_port_available(port, host="127.0.0.1")


def normalize_host_for_url(host: str) -> str:
    """
    将不可直连的通配地址转换为浏览器可访问地址。
    """
    normalized = (host or "").strip()
    if normalized in WILDCARD_HOSTS:
        return "127.0.0.1"
    return normalized


def build_launch_plan(
    *,
    api_host: str,
    api_port: int,
    webui_host: str,
    webui_port: int,
    is_port_available: Callable[[int], bool] | None = None,
) -> Dict[str, object]:
    """
    生成统一启动器所需的端口与地址配置。
    """
    checker = is_port_available or is_port_available_on_localhost
    selected_api_port = choose_available_port(api_port, is_port_available=checker)
    selected_webui_port = choose_available_port(webui_port, is_port_available=checker)
    api_url_host = normalize_host_for_url(api_host)

    return {
        "api_host": api_host,
        "api_port": selected_api_port,
        "webui_host": webui_host,
        "webui_port": selected_webui_port,
        "openai_base_url": f"http://{api_url_host}:{selected_api_port}{DEFAULT_API_PATH}",
    }


def main() -> None:
    """
    从环境变量读取基础端口配置，并输出 JSON 结果给启动脚本消费。
    """
    plan = build_launch_plan(
        api_host=os.environ.get("API_HOST", "0.0.0.0"),
        api_port=int(os.environ.get("API_PORT", "8000")),
        webui_host=os.environ.get("WEBUI_HOST", "127.0.0.1"),
        webui_port=int(os.environ.get("WEBUI_PORT", "7860")),
    )
    print(json.dumps(plan, ensure_ascii=True))


if __name__ == "__main__":
    main()
