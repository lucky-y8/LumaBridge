# LumaBridge User Manual

[中文操作手册](操作手册.zh-CN.md)

## 1. Purpose and transfer model

LumaBridge moves one file between isolated computers through an optical workflow:

1. The sending computer displays a looping stream of QR codes.
2. A phone records the screen; the phone does not need a companion app.
3. The recording is copied to the receiving computer by an approved local method.
4. LumaBridge scans one or more recordings, collects unique chunks, and verifies the result.

The application never connects to a server and does not include accounts, analytics, advertisements, or automatic updates.

The Codex-style light theme is enabled by default. Use **Switch to Dark Mode** at the bottom of the sidebar to switch to the optional dark interface; this does not change the QR playback background or encoded data.

## 2. Before you begin

- On Windows, keep `LumaBridge.exe` and the `_internal` directory together.
- Ensure the sending monitor can display the entire QR code without scaling or cropping.
- Ensure the phone has enough free storage for two playback loops.
- Disable beautification filters and avoid messaging-app recompression.
- Test the complete workflow with a small 10 KB file before transferring important data.

## 3. Send a file

1. Open **Send File**.
2. Drag one file into the window or select **Browse File**.
3. Wait for SHA-256 analysis to finish.
4. Review file size, chunk count, loop duration, and recommended recording time.
5. Select a profile:
   - **Stable:** 500-byte chunks at 2 fps for glare, small screens, or weaker cameras.
   - **Standard:** 700-byte chunks at 3 fps; recommended default.
   - **Fast:** 800-byte chunks at 4 fps for a sharp display and stable camera.
   - **Custom:** 200–1000 bytes and 0.5–8 fps.
6. Keep the three-second countdown enabled when another person operates the phone.
7. Select two loops or unlimited playback.
8. Choose **Start Full-screen Playback**.

### Full-screen controls

| Key | Action |
| --- | --- |
| `Esc` | Stop playback and return to the application |
| `Space` | Pause or continue |
| `Left` / `Right` | Pause and move to the previous or next chunk |

## 4. Record the QR stream

Recommended setup: hold the phone horizontally, record at 1080p/60 fps, and capture at least two complete loops.

For reliable recognition:

- Use a tripod or stable support and keep the lens parallel to the monitor.
- Keep the complete QR code and white quiet zone inside the frame.
- Tap the QR area to focus, then reduce exposure if white areas are overexposed.
- Avoid reflections, digital zoom, image stabilization crop, and moving shadows.
- If rolling dark bands appear, try 30 fps, lower monitor brightness, or a 1/60 shutter.
- If recognition remains weak, switch to the Stable profile.

## 5. Recover a file

1. Open **Recover File**.
2. Add MP4, MOV, AVI, MKV, M4V, or WebM recordings.
3. Remove unwanted entries or move recordings into the desired order.
4. Keep the recognition rate at 12 attempts/second initially. Use 20–30 only for difficult footage.
5. Choose **Start Scan**.
6. Watch both progress bars:
   - **Current video scan progress** shows how far the reader has moved through the video.
   - **Unique chunk collection progress** shows how much of the original file is available.
7. Pause, continue, or cancel when required. Collected chunks remain available.

A damaged or unsupported video is marked and skipped. A conflicting chunk stops safe recovery and must be investigated.

## 6. Incomplete recovery and supplementary recordings

If scanning ends before every chunk is collected:

1. Review the missing chunk count and one-based chunk numbers.
2. Choose **Save State** and store the `.qrstate` file safely.
3. Record another complete loop, preferably with improved focus or the Stable profile.
4. Reopen LumaBridge and choose **Load State**.
5. Add the supplementary video and start scanning again.

The state file contains recovered file chunks. Treat it with the same confidentiality as the original file. It uses JSON rather than Python Pickle and is saved through a temporary file plus atomic replacement.

## 7. Save the restored file

When every chunk is present, choose **Restore and Save File**. LumaBridge:

1. Sorts chunks by protocol index.
2. Reconstructs the exact declared file length.
3. Verifies final file size.
4. Verifies the complete SHA-256 hash.
5. Writes a temporary file and atomically renames it only after verification.

An existing target is never overwritten silently. Do not trust a result unless LumaBridge explicitly reports successful size and SHA-256 verification.

## 8. Progress and counters

- **Decoded QR:** readable QRF1 codes seen in sampled frames.
- **Added:** new unique chunks accepted for the active file.
- **Duplicate:** already collected chunks with identical content; safe and expected across loops.
- **CRC error:** decoded chunks whose data fails its CRC32 value; rejected.
- **Other file:** valid QRF1 chunks belonging to another session; ignored.
- **ETA:** an estimate based on current video scan speed, not chunk collection speed.

## 9. Troubleshooting

### No QR code is recognized

Confirm that the video contains LumaBridge/QRF1 codes, the complete quiet zone is visible, and focus is sharp. Increase attempts per second or record again with the Stable profile.

### Progress stops near completion

If video progress still changes, the application is not frozen; the remaining chunks have not been recognized. Let the video finish, save state, and add a supplementary recording.

### A video cannot be opened

The packaged OpenCV/FFmpeg build may not support its codec. Convert the video to a normal H.264 MP4 without resizing or cropping the QR image.

### SHA-256 does not match

LumaBridge refuses to report success. Keep the state file and scan a clean recording. Never use the temporary or incomplete output as the original file.

## 10. Logs and privacy

Choose **Task Log** to view user-facing activity and **Open Log Directory** for rotating technical logs. Logs contain errors and counters, but not complete QR payloads or original file content. LumaBridge performs no network requests during normal operation.
