#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

python -m pytest -q
python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name LumaBridge \
  --icon "$PROJECT_ROOT/src/optical_transfer/assets/lumabridge.png" \
  --add-data "$PROJECT_ROOT/src/optical_transfer/assets:optical_transfer/assets" \
  --paths "$PROJECT_ROOT/src" \
  --collect-all zxingcpp \
  --collect-all cv2 \
  "$PROJECT_ROOT/scripts/run_app.py"

cp README*.md LICENSES.md CHANGELOG.md dist/LumaBridge/
cp -r docs dist/LumaBridge/docs
echo "构建完成：$PROJECT_ROOT/dist/LumaBridge"
