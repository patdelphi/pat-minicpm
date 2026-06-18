# 单窗口前后端启动设计

## 背景

当前 `"scripts/start_stack.ps1"` 通过 `Start-Process` 分别打开两个新窗口来启动 API 和 WebUI。  
新的目标是保持单一入口，并且在同一个控制台窗口内完成前后端启动与运行。

## 目标

- 保留 `"scripts/start_stack.bat"` 作为统一入口
- 启动时仍然自动探测 API / WebUI 可用端口
- API 与 WebUI 在同一个窗口中前台运行
- 主窗口持续输出两边日志，并通过前缀区分来源
- 关闭主窗口时，两个子进程一起退出

## 非目标

- 不重构 `"scripts/start_api.ps1"` 与 `"scripts/start_webui.ps1"` 的单服务职责
- 不引入新的常驻 supervisor 服务
- 不修改 API / WebUI 业务逻辑

## 方案

采用单窗口双子进程方案：

1. `"scripts/start_stack.ps1"` 先沿用现有端口探测逻辑，计算实际的 `API_PORT`、`WEBUI_PORT`、`OPENAI_BASE_URL`
2. 主脚本在同一 PowerShell 会话中启动两个子进程：
   - API：调用项目内 Python 启动 `uvicorn`
   - WebUI：调用项目内 Python 启动 `"webui/gradio_app.py"`
3. 两个子进程都重定向标准输出与标准错误到主脚本
4. 主脚本循环读取输出，按来源打印：
   - `[API] ...`
   - `[WEBUI] ...`
5. 当任一子进程异常退出时，主脚本打印状态，并结束另一个子进程，避免残留孤儿进程
6. `"scripts/start_stack.bat"` 保持为单入口，仅负责调用 `"scripts/start_stack.ps1"`

## 文件变更

- `"scripts/start_stack.ps1"`
  - 从“开两个新窗口”改为“同窗口托管两个子进程”
  - 增加子进程生命周期管理与日志转发
- `"scripts/start_stack.bat"`
  - 调整提示文案，移除“new windows”描述
- 测试
  - 增加对启动策略文本或辅助函数的单测

## 错误处理

- 端口探测失败：直接退出，并输出英文错误
- Python 不存在：直接退出，并提示先安装项目内 Python
- API 或 WebUI 任一启动失败：主脚本输出失败来源，并清理另一个子进程
- 主脚本被关闭：尝试终止两个子进程，避免端口残留占用

## 测试计划

- 保留现有端口顺延测试
- 新增单窗口启动逻辑相关测试
- 手动验证：
  - 执行 `"scripts/start_stack.bat"`
  - 确认只出现一个窗口
  - 确认窗口中能看到 `[API]` / `[WEBUI]` 日志
  - 确认关闭窗口后端口被释放

## 风险与取舍

- 同窗口日志会混合输出，可读性不如分窗口，但更符合单窗口要求
- 如果后续需要更细粒度的进程守护，再考虑单独 supervisor；当前阶段没有必要增加复杂度
