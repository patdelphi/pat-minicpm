# API 说明

本文档用于说明当前仓库相关的 API 使用方式，并补充本次本地交付实现。

## 1. 官方托管 API 概览

如果使用官方托管服务，请以官方平台最新文档为准，典型调用形态如下：

```text
Base URL: https://api.modelbest.cn/v1
Chat API: POST /chat/completions
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

常见模型 ID 示例：

```text
MiniCPM-V-4.6-Instruct
MiniCPM-V-4.6-Thinking
MiniCPM-o-4.5
```

说明：

- 请使用你自己的 API Key
- 不要把真实密钥写入仓库或文档
- 官方能力、配额、模型列表可能随时间调整

## 2. 本仓库的本地 API 实现

本次交付重点是本地化运行 `MiniCPM-V 4.6 Thinking`，因此仓库新增了 OpenAI 兼容本地服务。

本地接口：

```text
GET  /health
GET  /v1/models
POST /v1/chat/completions
```

默认本地地址：

```text
http://127.0.0.1:8000/v1
```

## 3. 本地 Chat Completions 请求格式

文本请求示例：

```json
{
  "model": "openbmb/MiniCPM-V-4.6-Thinking-BNB",
  "messages": [
    {
      "role": "user",
      "content": "请用一句话介绍你自己。"
    }
  ],
  "stream": false
}
```

图文请求示例：

```json
{
  "model": "openbmb/MiniCPM-V-4.6-Thinking-BNB",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "请描述这张图片。"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,<BASE64_IMAGE>"
          }
        }
      ]
    }
  ],
  "stream": false
}
```

视频请求示例：

```json
{
  "model": "openbmb/MiniCPM-V-4.6-Thinking-BNB",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "video_url",
          "video_url": {
            "url": "file:///Y:/videos/demo.mp4"
          }
        },
        {
          "type": "text",
          "text": "请概括这个视频的主要内容。"
        }
      ]
    }
  ],
  "stream": false
}
```

## 4. 本地实现差异

为了让本地 `Thinking` 模型更适合终端使用，当前实现做了以下处理：

- 默认补充中文 system 提示
- 默认关闭可见思考过程：`enable_thinking=False`
- 使用停止词 `248044`、`248046`
- 输出阶段过滤 `<think>` 内容

## 5. 多模态输入说明

图片支持：

- `data:` URL
- `file://` URL
- 本地路径

视频支持：

- 通过 `video_url` 传入
- 本地用 `ffmpeg` / `ffprobe` 抽取代表帧
- 以多图形式送给模型

音频支持：

- API 可以接收 `audio_url`
- 当前会返回占位提示，不做真实音频语义理解

## 6. Python 调用示例

```python
"""
程序说明：调用本地 OpenAI 兼容接口，发送一条文本请求。
"""

import json
import urllib.request

payload = {
    "model": "openbmb/MiniCPM-V-4.6-Thinking-BNB",
    "messages": [
        {
            "role": "user",
            "content": "请列出 MiniCPM-V 的三个典型用途。",
        }
    ],
    "stream": False,
}

request = urllib.request.Request(
    "http://127.0.0.1:8000/v1/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(request) as response:
    data = json.loads(response.read().decode("utf-8"))

print(data["choices"][0]["message"]["content"])
```
