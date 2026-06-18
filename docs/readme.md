# MiniCPM-V 4.6 本地交付说明

## 1. 说明

本文档用于说明当前仓库新增的本地交付能力。
它是对上游项目的本地化补充，不替代原始 `"README.md"` 或 `"README_zh.md"`。

当前交付范围包括：

- 项目内独立 Python 3.11 运行时：`"tools/python311"`
- 本地模型目录支持：`"models/"`
- OpenAI 兼容本地 API
- 本地 Gradio WebUI
- 单窗口前后端统一启动脚本
- 图片解析支持
- 视频解析支持
- 纯音频上传占位提示

## 2. 目录结构

本次交付涉及的关键目录和文件如下：

- `"tools/python311"`：项目内 Python 运行时
- `"config/local.env"`：本地运行配置
- `"scripts/install.ps1"`：安装依赖脚本
- `"scripts/start_api.ps1"`：API 启动脚本
- `"scripts/start_webui.ps1"`：WebUI 启动脚本
- `"scripts/start_stack.bat"`：统一启动入口
- `"scripts/start_stack.ps1"`：统一启动逻辑
- `"api/"`：本地 OpenAI 兼容 API 实现
- `"webui/"`：本地 Gradio WebUI
- `"aipython/"`：下载、量化、端口选择、媒体处理等辅助脚本

## 3. 当前默认配置

默认配置来自 `"config/local.env"`：

- `MODEL_ID=openbmb/MiniCPM-V-4.6-Thinking-BNB`
- `MODEL_DIR=models/MiniCPM-V-4.6-Thinking`
- `QUANT_DIR=models/MiniCPM-V-4.6-Thinking-int4`
- `API_PORT=8000`
- `WEBUI_PORT=7863`
- `MAX_NEW_TOKENS=1024`

其中 `Thinking` 模型的本地推理已和官方推荐行为对齐：

- 使用 `enable_thinking=False`
- 使用停止词 `248044`、`248046`

这样可以避免把思考过程直接暴露给前端，同时减少回答被截断的问题。

## 4. 输入能力

当前本地交付支持的输入类型如下：

- 图片：支持
- 视频：支持
- 纯音频：当前仅返回占位提示

视频处理策略：

- API 支持 `video_url`
- 本地辅助模块使用 `ffmpeg` / `ffprobe`
- 视频会先被抽帧
- 抽出的代表帧再作为多图输入送入模型

音频处理策略：

- WebUI 可以选择音频文件
- API 可以接收 `audio_url`
- 当前部署基于 `MiniCPM-V 4.6`，不具备原生纯音频理解能力，因此返回友好提示，而不是报错中断

## 5. 安装

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/install.ps1"
```

安装脚本会完成以下工作：

- 如有需要，安装项目内 Python 3.11
- 升级 `pip`
- 安装 `torch`
- 安装 `"requirements_local.txt"` 中的依赖

## 6. 启动方式

### 方式 A：统一启动

直接双击或执行：

```bat
"scripts\start_stack.bat"
```

行为说明：

- 在同一个窗口里启动 API 和 WebUI
- API 端口从 `8000` 开始自动顺延
- WebUI 端口从 `7860` 开始自动顺延
- 脚本返回后窗口仍会保留，便于查看错误信息

### 方式 B：分别启动

启动 API：

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_api.ps1"
```

启动 WebUI：

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_webui.ps1"
```

## 7. API 端点

本地主要端点如下：

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

默认本地 OpenAI 兼容基础地址示例：

```text
http://127.0.0.1:8000/v1
```

如果统一启动器自动顺延了端口，请以控制台实际输出为准。

## 8. WebUI 说明

当前 WebUI 支持：

- 图片上传
- 视频上传
- 音频文件选择并返回占位提示
- 中文回答偏好
- 自动过滤思考过程输出

## 9. 已知限制

- 纯音频理解尚未实现
- 视频理解当前为抽帧方案，不是端到端原生视频解码
- `"models/"` 下的大模型文件不适合直接纳入常规源码仓库
- 本地运行时依赖与下载资产建议通过 `.gitignore` 隔离

## 10. 后续建议

- 如需真实音频理解，可考虑接入 ASR 或迁移到 `MiniCPM-o`
- 如需长期维护，建议继续细化本地 `.gitignore` 与发布流程
- 如需团队协作，建议把本地安装、运行、排障文档继续拆分细化
