$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$AppName = "LumaBridge-v1.0.1"
Set-Location $ProjectRoot

python -m pytest -q
python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onedir `
  --name $AppName `
  --icon "$ProjectRoot\src\optical_transfer\assets\lumabridge.ico" `
  --add-data "$ProjectRoot\src\optical_transfer\assets;optical_transfer/assets" `
  --paths "$ProjectRoot\src" `
  --collect-all zxingcpp `
  --collect-all cv2 `
  "$ProjectRoot\scripts\run_app.py"

Copy-Item "$ProjectRoot\README*.md" "$ProjectRoot\dist\$AppName" -Force
Copy-Item "$ProjectRoot\LICENSES.md" "$ProjectRoot\dist\$AppName\LICENSES.md" -Force
Copy-Item "$ProjectRoot\CHANGELOG.md" "$ProjectRoot\dist\$AppName\CHANGELOG.md" -Force
Copy-Item "$ProjectRoot\docs" "$ProjectRoot\dist\$AppName\docs" -Recurse -Force
Write-Host "构建完成：$ProjectRoot\dist\$AppName"
