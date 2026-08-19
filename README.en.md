# LumaBridge — Offline Optical File Transfer

[简体中文](README.zh-CN.md) · [User manual](docs/USER_MANUAL.en.md)

LumaBridge transfers a file between isolated computers by displaying a looping QR-code stream and scanning a phone recording. The application is designed for environments where networking, Wi-Fi, Bluetooth, and USB are unavailable or prohibited.

## Highlights

- Unified PySide6 desktop UI for sending and recovery.
- Codex-inspired white interface by default, with an optional dark theme using `#1F2937` for navigation and `#111827` for the main panel.
- Backward-compatible `QRF1` protocol.
- Stable, Standard, Fast, and Custom sending profiles.
- Responsive full-screen QR player with countdown, looping, pause, and manual stepping.
- Multiple-video recovery queue with pause, cancel, ordering, and damaged-video isolation.
- Separate video-scan and unique-chunk progress indicators.
- Duplicate filtering and hard failure on conflicting chunks.
- CRC32 per chunk plus final file-size and SHA-256 verification.
- Atomic, versioned JSON `.qrstate` files for interrupted recovery.
- Atomic output writing without silent overwrite.
- Local rotating logs that never contain complete QR payloads.

## Quick start

### Windows portable build

Open `LumaBridge.exe` inside the complete `LumaBridge` release directory. Keep the `_internal` directory next to the executable.

The application opens in the Codex-style light theme. Use **Switch to Dark Mode** in the sidebar whenever you prefer the dark palette.

### Conda source environment

```powershell
conda create -n lumabridge python=3.11 -y
conda activate lumabridge
python -m pip install -e ".[dev]"
python -m optical_transfer
```

Dependency installation requires a network connection. Sending, scanning, state storage, and restoration are fully offline afterwards.

## Recommended recording setup

Hold the phone horizontally, record at 1080p/60 fps, and capture at least two complete playback loops. Keep the camera fixed, the QR code fully visible, and exposure low enough to preserve the white quiet zone.

See the [English User Manual](docs/USER_MANUAL.en.md) for the complete workflow, troubleshooting, progress meanings, and recovery-state instructions.

## Tests

```powershell
conda activate py311
python -m pytest -q
```

The test suite covers protocol parsing, CRC errors, Unicode names, empty files, duplicate and conflict handling, state integrity, final restoration, real QR recognition, video scanning, and low-resolution player layout.

## Build

Build Windows artifacts on Windows x64:

```powershell
.\scripts\build_windows.ps1
```

Build Linux artifacts on the target Linux x64 distribution:

```bash
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh
```

PyInstaller artifacts cannot be reused across operating systems. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md), [LICENSES.md](LICENSES.md), and the original [software requirements](动态二维码离线文件传输软件需求文档.md).

## Architecture

Protocol and recovery logic under `src/optical_transfer/` is independent from Qt widgets. `sender/` owns chunking, QR generation, and playback; `receiver/` owns video scanning, collection, state, and restoration; `ui/` coordinates the desktop interface.
