# MiniCPM-V 4.6 Local Delivery README

## 1. Overview

This file documents the local delivery work added on top of the upstream project.
It does not replace the original `"README.md"` or `"README_zh.md"`.

Current local delivery scope:

- Project-local Python 3.11 under `"tools/python311"`
- Local model path support under `"models/"`
- OpenAI-compatible local API
- Local Gradio WebUI
- Single-window startup script
- Image parsing support
- Video parsing support
- Audio upload placeholder response

## 2. Local Runtime Layout

Key local directories and files:

- `"tools/python311"`: project-local Python runtime
- `"config/local.env"`: local runtime configuration
- `"scripts/install.ps1"`: local dependency install script
- `"scripts/start_api.ps1"`: API startup script
- `"scripts/start_webui.ps1"`: WebUI startup script
- `"scripts/start_stack.bat"`: unified single-window launcher
- `"scripts/start_stack.ps1"`: unified single-window launcher logic
- `"api/"`: local OpenAI-compatible API implementation
- `"webui/"`: local Gradio WebUI
- `"aipython/"`: local helper scripts

## 3. Current Model Configuration

Default local configuration from `"config/local.env"`:

- `MODEL_ID=openbmb/MiniCPM-V-4.6-Thinking-BNB`
- `MODEL_DIR=models/MiniCPM-V-4.6-Thinking`
- `QUANT_DIR=models/MiniCPM-V-4.6-Thinking-int4`
- `API_PORT=8000`
- `WEBUI_PORT=7863`
- `MAX_NEW_TOKENS=1024`

The local runtime aligns the Thinking checkpoint with:

- `enable_thinking=False`
- stop token IDs `[248044, 248046]`

This avoids incomplete visible reasoning output and keeps final answers cleaner.

## 4. Supported Inputs

Current local input support:

- Image: supported
- Video: supported
- Pure audio: not supported by MiniCPM-V 4.6 in this delivery

Video handling strategy:

- The API accepts `video_url`
- The local helper uses `ffmpeg` / `ffprobe`
- The video is converted into representative frames
- The frames are then sent to the model as multi-image input

Audio handling strategy:

- The WebUI can select audio files
- The API can receive `audio_url`
- The current response is a placeholder message because MiniCPM-V 4.6 does not provide native pure-audio understanding in this delivery

## 5. Installation

Run in PowerShell from the project root:

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/install.ps1"
```

What the installer does:

- installs project-local Python 3.11 if needed
- upgrades `pip`
- installs `torch`
- installs packages from `"requirements_local.txt"`

## 6. Start Services

### Option A: Unified Start

Run:

```bat
"scripts\start_stack.bat"
```

Behavior:

- starts API and WebUI from one window
- auto-selects the next available API port starting from `8000`
- auto-selects the next available WebUI port starting from `7860`
- keeps the console window open after the script returns

### Option B: Start Separately

Start API:

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_api.ps1"
```

Start WebUI:

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_webui.ps1"
```

## 7. API Endpoints

Main endpoints:

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

OpenAI-compatible local base URL example:

```text
http://127.0.0.1:8000/v1
```

## 8. WebUI Notes

The local WebUI currently supports:

- image file upload
- video file upload
- audio file selection with placeholder response
- Chinese answer preference
- thinking output suppression for end users

If the unified launcher chooses a different port, use the port shown in the console.

## 9. Known Limitations

- Pure audio understanding is not implemented in this delivery
- Video understanding is frame-based, not native end-to-end video decoding inside the API layer
- Large local models under `"models/"` are not suitable for normal source control push
- The working tree currently contains many local runtime artifacts and downloaded assets

## 10. Recommended Next Steps

- add a dedicated local `.gitignore` strategy before long-term maintenance
- separate delivery docs from upstream docs more clearly
- decide whether pure audio should use ASR or migrate to `MiniCPM-o`
- refine startup supervision and shutdown cleanup further if needed
