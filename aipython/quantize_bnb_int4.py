"""
程序说明：
对 MiniCPM-V 4.6（Thinking）进行 bitsandbytes int4 量化，并保存到本地目录。
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import torch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True, help="原始模型目录，例如：models/MiniCPM-V-4.6-Thinking")
    parser.add_argument("--output-dir", required=True, help="量化后输出目录，例如：models/MiniCPM-V-4.6-Thinking-int4")
    parser.add_argument("--device", default="cuda", help="默认 cuda")
    parser.add_argument("--max-new-tokens", type=int, default=64, help="用于快速自检的生成长度")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        print("CUDA 不可用，BNB int4 量化需要 GPU。", file=sys.stderr)
        return 2

    model_dir: str = args.model_dir
    output_dir: str = args.output_dir

    try:
        from transformers import BitsAndBytesConfig
        from transformers.models.minicpmv4_6.modeling_minicpmv4_6 import MiniCPMV4_6ForConditionalGeneration
        from transformers.models.minicpmv4_6.processing_minicpmv4_6 import MiniCPMV4_6Processor
        from PIL import Image
    except Exception as e:
        print(f"依赖导入失败：{e}", file=sys.stderr)
        return 2

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        load_in_8bit=False,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_storage=torch.uint8,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        llm_int8_enable_fp32_cpu_offload=False,
        llm_int8_has_fp16_weight=False,
        llm_int8_skip_modules=["lm_head"],
        llm_int8_threshold=6.0,
    )

    try:
        processor = MiniCPMV4_6Processor.from_pretrained(model_dir)
        model = MiniCPMV4_6ForConditionalGeneration.from_pretrained(
            model_dir,
            device_map=args.device,
            quantization_config=quantization_config,
        )

        image_path = os.path.join("assets", "airplane.jpeg")
        if not os.path.exists(image_path):
            image_path = None

        messages = [
            {
                "role": "user",
                "content": [],
            }
        ]
        if image_path:
            image = Image.open(image_path).convert("RGB")
            messages[0]["content"].append({"type": "image", "image": image})
        messages[0]["content"].append({"type": "text", "text": "请用一句话描述这张图。"})

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)

        start = time.time()
        out_ids = model.generate(**inputs, max_new_tokens=args.max_new_tokens)
        response = processor.decode(
            out_ids[0][inputs["input_ids"].shape[-1] :],
            skip_special_tokens=True,
        )
        print("量化自检输出：", response)
        print("量化自检耗时：", time.time() - start)

        os.makedirs(output_dir, exist_ok=True)
        model.save_pretrained(output_dir, safe_serialization=True)
        processor.save_pretrained(output_dir)
        print(f"量化并保存完成：{output_dir}")
        return 0
    except Exception as e:
        print(f"量化失败：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

