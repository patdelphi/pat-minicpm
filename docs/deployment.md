# 部署与运行（Windows / NVIDIA GPU）

## 1. 配置

- 默认配置在 `"config/local.env"`
- 默认模型：`openbmb/MiniCPM-V-4.6-Thinking-BNB`

如需切换模型，修改 `"config/local.env"` 的 `MODEL_ID`，例如：
- `openbmb/MiniCPM-V-4.6-BNB`
- `openbmb/MiniCPM-V-4.6`

## 2. 安装依赖

说明：
- 安装脚本会自动下载并安装项目内 Python 3.11（不写入系统全局）
- 仍然需要可访问外网（python.org / pypi.org / huggingface.co）

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/install.ps1"
```

说明：
- 依赖清单在 `"requirements_local.txt"`
- 若 `bitsandbytes` 在 Windows 安装失败：可先把 `"requirements_local.txt"` 里的 `bitsandbytes` 删除后重装，并把模型切到非 BNB 版本验证链路

## 3. 启动 API（OpenAI 兼容）

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_api.ps1"
```

API 端点：
- `POST http://127.0.0.1:8000/v1/chat/completions`

## 4. 启动 WebUI

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_webui.ps1"
```

浏览器打开（默认）：
- `http://127.0.0.1:7860`
