# 部署与运行（Windows / NVIDIA GPU）

## 1. 配置

- 默认配置在 `"config/local.env"`
- 默认模型：`openbmb/MiniCPM-V-4.6-Thinking-BNB`
- 默认 API 端口：`8000`
- 默认 WebUI 端口：`7863`

如需切换模型，修改 `"config/local.env"` 的 `MODEL_ID`，例如：
- `openbmb/MiniCPM-V-4.6-BNB`
- `openbmb/MiniCPM-V-4.6`

## 2. 安装依赖

说明：
- 安装脚本会自动下载并安装项目内 Python 3.11（不写入系统全局）
- 仍然需要可访问外网（python.org / pypi.org / huggingface.co）
- 下载模型、量化模型时需要额外的磁盘空间

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/install.ps1"
```

说明：
- 依赖清单在 `"requirements_local.txt"`
- 若 `bitsandbytes` 在 Windows 安装失败：可先把 `"requirements_local.txt"` 里的 `bitsandbytes` 删除后重装，并把模型切到非 BNB 版本验证链路

## 3. 下载模型

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/download_model.ps1"
```

说明：
- 默认下载到 `"models/MiniCPM-V-4.6-Thinking"`
- 如需切换模型，可先修改 `"config/local.env"` 中的模型配置

## 4. 量化为 int4（可选）

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/quantize_int4.ps1"
```

说明：
- 默认输出目录为 `"models/MiniCPM-V-4.6-Thinking-int4"`
- 如显存足够，也可以直接使用非量化模型目录

## 5. 启动 API（OpenAI 兼容）

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_api.ps1"
```

默认接口：
- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/v1/models`
- `POST http://127.0.0.1:8000/v1/chat/completions`

## 6. 启动 WebUI

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_webui.ps1"
```

浏览器打开（默认）：
- `http://127.0.0.1:7863`

## 7. 单窗口统一启动

如果希望一个窗口同时启动前后端，执行：

```bat
"scripts\start_stack.bat"
```

行为说明：

- 自动为 API 和 WebUI 选择可用端口
- 当前窗口直接输出 `[API]` / `[WEBUI]` 日志
- 脚本退出后窗口会保留，便于查看错误

## 8. 输入能力

当前本地交付支持：

- 图片解析
- 视频解析
- 纯音频文件选择与占位提示

说明：
- 视频通过 `ffmpeg` / `ffprobe` 抽帧后再送入模型
- 纯音频不是 `MiniCPM-V 4.6` 的原生能力，当前不做真实语义理解
