"""
程序说明：
加载 MiniCPM-V 4.6（优先加载本地 int4 量化目录），并提供一次推理函数。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import torch

from transformers.models.minicpmv4_6.modeling_minicpmv4_6 import MiniCPMV4_6ForConditionalGeneration
from transformers.models.minicpmv4_6.processing_minicpmv4_6 import MiniCPMV4_6Processor

DEFAULT_STOP_TOKEN_IDS = [248044, 248046]


class ModelRuntime:
    def __init__(self, model_dir: str, quant_dir: str) -> None:
        self.model_dir = model_dir
        self.quant_dir = quant_dir
        self._processor: Optional[MiniCPMV4_6Processor] = None
        self._model: Optional[MiniCPMV4_6ForConditionalGeneration] = None

    def _pick_dir(self) -> str:
        if os.path.exists(self.quant_dir) and os.path.exists(os.path.join(self.quant_dir, "config.json")):
            return self.quant_dir
        return self.model_dir

    def load(self) -> None:
        if self._model is not None and self._processor is not None:
            return

        path = self._pick_dir()
        self._processor = MiniCPMV4_6Processor.from_pretrained(path)

        if torch.cuda.is_available():
            device_map = "cuda"
            dtype = torch.bfloat16
        else:
            device_map = "cpu"
            dtype = torch.float32

        self._model = MiniCPMV4_6ForConditionalGeneration.from_pretrained(
            path,
            device_map=device_map,
            torch_dtype=dtype,
        )
        self._model.eval()

    def _get_stop_token_ids(self) -> List[int]:
        """
        读取模型生成配置中的停止词；若配置缺失，则回退到官方文档给出的 v4.6 停止词。
        """
        assert self._model is not None

        eos_token_id = getattr(getattr(self._model, "generation_config", None), "eos_token_id", None)
        if isinstance(eos_token_id, int):
            return [int(eos_token_id)]
        if isinstance(eos_token_id, (list, tuple)) and eos_token_id:
            return [int(token_id) for token_id in eos_token_id]
        return DEFAULT_STOP_TOKEN_IDS.copy()

    def infer(self, messages: List[Dict[str, Any]], max_new_tokens: int) -> str:
        self.load()
        assert self._processor is not None
        assert self._model is not None

        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            enable_thinking=False,
        ).to(self._model.device)

        out_ids = self._model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            eos_token_id=self._get_stop_token_ids(),
        )
        prompt_len = inputs["input_ids"].shape[-1]
        text = self._processor.decode(out_ids[0][prompt_len:], skip_special_tokens=True)
        return text
