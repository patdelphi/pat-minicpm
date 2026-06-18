# 本地 API（OpenAI 兼容）

当前本地服务不是直接使用 `transformers serve`，而是基于自定义 `"api/"` 模块实现的 OpenAI 兼容接口。

关键特点：

- 启动脚本：`"scripts/start_api.ps1"`
- 默认监听：`0.0.0.0:8000`
- 主要接口：`/health`、`/v1/models`、`/v1/chat/completions`
- 默认使用中文回答，并过滤思考过程输出

## 1. 启动

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File "scripts/start_api.ps1"
```

默认本地地址：

```text
http://127.0.0.1:8000/v1
```

## 2. Chat Completions

请求地址：

```text
POST http://127.0.0.1:8000/v1/chat/completions
```

当前限制：

- 仅支持 `stream=false`
- 支持文本、图片、视频
- 纯音频当前返回占位提示

图文请求示例：

```json
{
  "model": "openbmb/MiniCPM-V-4.6-Thinking-BNB",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,...."
          }
        },
        {
          "type": "text",
          "text": "这张图里有什么？"
        }
      ]
    }
  ],
  "stream": false,
  "max_tokens": 1024
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
          "text": "请总结这个视频的主要内容。"
        }
      ]
    }
  ],
  "stream": false
}
```

## 3. 返回说明

成功响应遵循 OpenAI Chat Completions 风格，关键结果位于：

```json
choices[0].message.content
```

本地实现会额外做两件事：

- 自动补默认中文 system 提示
- 去除 `<think>...</think>` 以及残留思考标签

## 4. 媒体处理说明

图片支持：

- `data:` URL
- `file://` URL
- 本地路径

视频支持：

- `video_url`
- 使用 `ffmpeg` / `ffprobe` 抽帧
- 以多图形式送入模型推理

音频支持：

- `audio_url`
- 当前不做真实语义理解，仅返回友好占位消息
