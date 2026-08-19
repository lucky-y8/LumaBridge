# Changelog

## 1.0.1 — 2026-08-19

### English

- Moved scan percentages beside the progress bars so the filled track cannot cover them.
- Added **Restore Defaults** to both Send File and Recover File settings.
- Rebuilt the Windows executable with the embedded multi-size fox icon and a stable `LumaBridge.exe` filename.
- Added Windows application identity and version resources so Explorer, shortcuts, and the taskbar consistently use the fox icon.

### 简体中文

- 将扫描百分比独立显示在进度条右侧，避免填充条覆盖进度文字。
- 在“发送文件”和“恢复文件”页面都增加“恢复默认设置”。
- 使用稳定的 `LumaBridge.exe` 文件名和内嵌多尺寸小狐狸图标重新构建 Windows 程序。
- 增加 Windows 应用身份与版本资源，使资源管理器、快捷方式和任务栏稳定显示小狐狸图标。

## 1.0.0 — 2026-08-19

### English

- Added the complete offline QRF1 sending and multi-video recovery workflow.
- Added chunk CRC32, final size/SHA-256 verification, conflict detection, and atomic output.
- Added versioned `.qrstate` recovery state with atomic persistence.
- Added responsive full-screen QR playback and low-resolution/high-DPI safeguards.
- Added a Codex-inspired white default UI and an optional dark theme with `#1F2937` navigation and `#111827` workspace colors.
- Added the orange fox transfer mark as the in-app logo, window icon, and Windows executable icon.
- Added separate English and Simplified Chinese README files and user manuals.
- Added Windows and Linux build scripts plus automated protocol, QR, video, state, and layout tests.

### 简体中文

- 完成离线 QRF1 发送与多录像恢复流程。
- 增加分片 CRC32、最终大小/SHA-256 校验、冲突检测和原子输出。
- 增加带版本号并原子保存的 `.qrstate` 恢复状态。
- 增加自适应全屏二维码播放，以及低分辨率和高 DPI 保护。
- 增加默认 Codex 风格白色界面，并可切换为导航 `#1F2937`、工作区 `#111827` 的深色主题。
- 将橙色小狐狸传输标识用于应用内 Logo、窗口图标和 Windows EXE 文件图标。
- 增加独立的英文、简体中文 README 和操作手册。
- 增加 Windows/Linux 构建脚本，以及协议、二维码、视频、状态和布局自动测试。
