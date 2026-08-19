# LumaBridge — Offline Optical File Transfer

[简体中文](README.zh-CN.md) · [User manual](docs/USER_MANUAL.en.md)

LumaBridge transfers a file between isolated computers by displaying a looping QR-code stream and scanning a phone recording. The application is designed for environments where networking, Wi-Fi, Bluetooth, and USB are unavailable or prohibited.

## Interface preview

| Send File | Recover File |
| --- | --- |
| ![LumaBridge Send File interface](docs/images/send.png) | ![LumaBridge Recover File interface](docs/images/recover.png) |

## Use cases

LumaBridge is intended for situations where two devices have no network, Bluetooth, or usable USB connection, but data can still be carried through a screen and a phone camera. Examples include:

- An offline computer cannot connect to the internet or a local network.
- Wi-Fi, Ethernet, Bluetooth, or USB hardware is unavailable or damaged.
- A small log, configuration, or installer file must enter or leave an isolated test environment.
- A temporary device lacks a compatible data interface.
- Installing a phone application is impractical, so only the standard camera is available.
- QR chunks must be collected across several recordings and restored later on another computer.

LumaBridge is best suited to small files ranging from a few KB to a few MB. QR playback and recording time increase significantly for large files; prefer a storage drive, local network, or another high-speed transfer method when one is available.

### Example

An offline Windows 11 computer cannot access a network and its USB ports are unavailable. A compressed archive of about 600 KB must be transferred to another computer.

1. Open LumaBridge on the offline computer and select **Send File**.
2. Select the archive and play the dynamic QR stream using Standard mode.
3. Record two complete loops with the phone held horizontally.
4. Take the recording to the other computer and open **Recover File** in LumaBridge.
5. Add the phone recording and start scanning.
6. LumaBridge recognizes, deduplicates, and collects QR chunks automatically.
7. After every chunk is collected, LumaBridge restores the original file and verifies its SHA-256 digest.
8. Use the restored archive only after the application reports successful recovery.

If the first recording is missing some chunks, save the recovery state, record an additional video, and continue scanning without starting over.

> Transfer only data that you own or are explicitly authorized to handle, and follow your organization’s security policies. Nearby cameras can read the QR display, so LumaBridge does not provide confidentiality by default.

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

Open `LumaBridge.exe` inside the complete release directory. Keep the `_internal` directory next to the executable.

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

PyInstaller artifacts cannot be reused across operating systems. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) and [LICENSES.md](LICENSES.md).

## Architecture

Protocol and recovery logic under `src/optical_transfer/` is independent from Qt widgets. `sender/` owns chunking, QR generation, and playback; `receiver/` owns video scanning, collection, state, and restoration; `ui/` coordinates the desktop interface.
