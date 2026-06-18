"""
程序说明：
校验统一启动脚本的关键约束：
1. 不再启动新的 PowerShell 窗口。
2. 在同一窗口内转发 API / WebUI 日志。
3. BAT 文案不再声明会打开新窗口。
"""

from pathlib import Path


def test_start_stack_ps1_uses_single_window_supervision():
    script = Path(r"y:\NewStore\AI\MiniCPM-V\scripts\start_stack.ps1").read_text(encoding="utf-8")

    assert 'Start-Process -FilePath "powershell"' not in script
    assert "RedirectStandardOutput" in script
    assert "RedirectStandardError" in script
    assert "TRAE_LOG_PREFIX" in script
    assert '"API"' in script
    assert '"WEBUI"' in script
    assert '$psi.ArgumentList' not in script
    assert '$psi.Arguments =' in script
    assert ".EnvironmentVariables" in script


def test_start_stack_bat_does_not_claim_new_windows():
    script = Path(r"y:\NewStore\AI\MiniCPM-V\scripts\start_stack.bat").read_text(encoding="utf-8")

    assert "new windows" not in script.lower()
    assert "-command" in script.lower()
    assert "pause" in script.lower()
