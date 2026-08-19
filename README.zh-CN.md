# LumaBridge — 光码离线文件传输

[English](README.en.md) · [中文操作手册](docs/操作手册.zh-CN.md)

LumaBridge 通过循环显示动态二维码并扫描手机录像，在隔离电脑之间传输文件，适用于无法使用网络、Wi-Fi、蓝牙或 USB 的环境。

## 主要功能

- PySide6 统一桌面界面，集成发送和恢复。
- 默认使用 Codex 风格白色界面，并可切换为侧栏 `#1F2937`、主面板 `#111827` 的深色主题。
- 向后兼容现有 `QRF1` 协议。
- 稳定、标准、快速和自定义发送模式。
- 自适应全屏二维码播放器，支持倒计时、循环、暂停和手动切片。
- 多录像恢复队列，支持排序、暂停、取消和损坏视频隔离。
- 视频扫描进度与唯一分片进度同时显示。
- 自动去重；同一编号出现不同内容时立即阻止恢复。
- 每个分片 CRC32，最终文件大小和 SHA-256 双重校验。
- 原子保存、带版本号的 JSON `.qrstate` 断点状态。
- 原子写入恢复文件，绝不静默覆盖已有文件。
- 本地滚动日志，不保存完整二维码载荷。

## 快速开始

### Windows 便携版

在完整的发布目录内运行 `LumaBridge-v1.0.1.exe`。不要把 EXE 单独移走，旁边的 `_internal` 目录是运行所必需的。

软件默认使用 Codex 风格浅色主题；如需深色界面，可点击侧栏底部的“切换深色模式”。

### Conda 源码环境

```powershell
conda create -n lumabridge python=3.11 -y
conda activate lumabridge
python -m pip install -e ".[dev]"
python -m optical_transfer
```

安装依赖时需要网络；安装完成后，发送、扫描、状态保存和恢复全部离线运行。

## 推荐录像方式

建议手机横屏、1080p/60fps 录像，并至少录制两个完整循环。固定手机，保证二维码完整入镜，并适当降低曝光以保留清晰白色静区。

完整步骤、进度说明、断点恢复和故障处理请阅读[中文操作手册](docs/操作手册.zh-CN.md)。

## 测试

```powershell
conda activate py311
python -m pytest -q
```

测试覆盖协议解析、CRC 错误、中文文件名、空文件、重复与冲突、状态完整性、最终恢复、二维码实际识别、视频扫描以及低分辨率播放器布局。

## 构建

Windows x64 必须在 Windows 上构建：

```powershell
.\scripts\build_windows.ps1
```

Linux x64 必须在目标 Linux 发行版上构建：

```bash
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh
```

不同系统的 PyInstaller 包不能交叉复用。其他信息见[已知问题](KNOWN_ISSUES.md)、[第三方许可证](LICENSES.md)和原始[软件需求文档](动态二维码离线文件传输软件需求文档.md)。

## 工程结构

`src/optical_transfer/` 下的协议与恢复逻辑不依赖 Qt 控件。`sender/` 负责分片、二维码生成和播放；`receiver/` 负责视频扫描、收集、状态和恢复；`ui/` 负责桌面界面协调。
