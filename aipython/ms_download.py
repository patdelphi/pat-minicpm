"""
程序说明：
从 ModelScope 下载指定模型到本项目内的本地目录（默认存到 "models/"）。
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True, help="例如：OpenBMB/MiniCPM-V-4.6-Thinking")
    parser.add_argument("--output-dir", required=True, help="例如：models/MiniCPM-V-4.6-Thinking")
    args = parser.parse_args()

    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except Exception as e:
        print(f"导入 modelscope 失败：{e}", file=sys.stderr)
        return 2

    model_id: str = args.model_id
    output_dir: str = args.output_dir

    try:
        os.makedirs(output_dir, exist_ok=True)
        local_dir = snapshot_download(model_id=model_id, local_dir=output_dir)
        print(f"下载完成：{model_id} -> {local_dir}")
        return 0
    except Exception as e:
        print(f"下载失败：{model_id} -> {output_dir}，原因：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
