# 本地 API（OpenAI 兼容）

本地服务端使用 Transformers 内置服务：
- 启动脚本：`"scripts/start_api.ps1"`
- 默认监听：`0.0.0.0:8000`
- 接口：`/v1/chat/completions`

## Chat Completions

Endpoint：
- `POST http://127.0.0.1:8000/v1/chat/completions`

示例请求（图文）：

```json
{
  "model": "openbmb/MiniCPM-V-4.6-Thinking-BNB",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,...."}},
        {"type": "text", "text": "这张图里有什么？"}
      ]
    }
  ],
  "stream": false
}
```

