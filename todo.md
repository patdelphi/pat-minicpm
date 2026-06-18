## 目标

- 本地运行 MiniCPM-V 4.6 Thinking BNB（或可替换为其他量化/非量化模型）
- 提供 OpenAI 兼容 API：`/v1/chat/completions`
- 提供本地 WebUI（优先 Gradio），支持上传图片 + 文本对话

## 待办（需你确认后执行）

- [x] 1. 仓库梳理：确认 4.6 推荐依赖（Transformers>=5.7.0）与现有 requirements 的冲突点，确定独立环境方案
- [x] 2. 安装项目内 Python 3.11 + 安装依赖：torch(CUDA)、transformers[serving]、accelerate、gradio、bitsandbytes（如需要）
- [x] 3. 实现本地启动脚本（Windows）：`"scripts/start_api.ps1"`、`"scripts/start_webui.ps1"`，统一从 `"config/local.env"` 读取端口/模型ID
- [x] 4. WebUI：新增 `"webui/gradio_app.py"`，调用本地 OpenAI 兼容 API（支持图片 `image_url` + 文本）
- [x] 5. 健康检查：新增最小 `/healthz`（如走自定义转发服务）或提供等价的启动自检脚本
- [x] 6. 测试（新增功能先写测试）：对 API 请求构造与连通性做 pytest（mock 或本地可选集成测试）
- [x] 7. 文档：创建 `"docs/"`（Windows 下与 `"Docs/"` 等价），补齐 `"docs/readme.md"`、`"docs/deployment.md"`、`"docs/local_api.md"`、`"docs/changelog.md"`
- [x] 8. 幂等校验：只跑 `lint/test/type-check/build`（按仓库现状选择可用项），确保 checks 全绿

## 音视频解析扩展（待确认后执行）

- [x] 9. 明确范围：仅 API 支持，还是 API + WebUI 一起支持
- [x] 10. 明确音频策略：纯音频是否需要真实语音内容解析，还是仅支持视频画面理解
- [x] 11. 设计多模态输入协议：补齐 `video_url` / 音频文件上传 / 本地文件转 data URL 的请求格式
- [x] 12. 媒体预处理：按需使用 `ffmpeg` 处理视频与音频输入，控制时长、采样和兼容性
- [x] 13. API 实现：扩展 `"api/openai_compat.py"` 与 `"api/app.py"` 的多模态解析和异常处理
- [x] 14. WebUI 实现：扩展 `"webui/gradio_app.py"`，增加音频/视频上传入口与请求构造
- [x] 15. 测试：先补单测，再补最小回归验证
- [x] 16. 文档：更新 `"docs/"` 中本地部署与 API 使用说明
