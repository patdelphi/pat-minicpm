"""
程序说明：
测试 MiniCPM-V 运行时的关键生成参数，确保 Thinking 模型不会默认展开思考过程，
并且会带上官方文档要求的停止词。
"""

from types import SimpleNamespace
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.model_runtime import ModelRuntime


class FakeBatch(dict):
    """模拟处理器返回的批量输入对象。"""

    def to(self, _device):
        return self


class FakeProcessor:
    def __init__(self) -> None:
        self.apply_kwargs = {}
        self.decode_kwargs = {}

    def apply_chat_template(self, *args, **kwargs):
        self.apply_kwargs = kwargs
        return FakeBatch({"input_ids": torch.tensor([[1, 2, 3]])})

    def decode(self, token_ids, **kwargs):
        self.decode_kwargs = {
            "token_ids": token_ids.tolist(),
            **kwargs,
        }
        return "最终答案"


class FakeModel:
    def __init__(self, eos_token_id) -> None:
        self.device = "cpu"
        self.generate_kwargs = {}
        self.generation_config = SimpleNamespace(eos_token_id=eos_token_id)

    def generate(self, **kwargs):
        self.generate_kwargs = kwargs
        return torch.tensor([[1, 2, 3, 4, 5]])


def test_infer_disables_thinking_and_uses_stop_tokens():
    runtime = ModelRuntime(model_dir="unused", quant_dir="unused")
    runtime._processor = FakeProcessor()
    runtime._model = FakeModel([248044, 248046])

    out = runtime.infer([{"role": "user", "content": "你好"}], max_new_tokens=1024)

    assert out == "最终答案"
    assert runtime._processor.apply_kwargs["enable_thinking"] is False
    assert runtime._model.generate_kwargs["max_new_tokens"] == 1024
    assert runtime._model.generate_kwargs["eos_token_id"] == [248044, 248046]
    assert runtime._processor.decode_kwargs["token_ids"] == [4, 5]
    assert runtime._processor.decode_kwargs["skip_special_tokens"] is True


def test_infer_falls_back_to_builtin_stop_tokens_when_config_is_missing():
    runtime = ModelRuntime(model_dir="unused", quant_dir="unused")
    runtime._processor = FakeProcessor()
    runtime._model = FakeModel(None)

    runtime.infer([{"role": "user", "content": "你好"}], max_new_tokens=256)

    assert runtime._model.generate_kwargs["eos_token_id"] == [248044, 248046]
