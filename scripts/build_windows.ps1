$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$AppName = "LumaBridge"
Set-Location $ProjectRoot

python -m pytest -q
python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onedir `
  --name $AppName `
  --icon "$ProjectRoot\src\optical_transfer\assets\lumabridge.ico" `
  --version-file "$ProjectRoot\scripts\windows_version_info.txt" `
  --add-data "$ProjectRoot\src\optical_transfer\assets;optical_transfer/assets" `
  --paths "$ProjectRoot\src" `
  --collect-all zxingcpp `
  --collect-all cv2 `
  "$ProjectRoot\scripts\run_app.py"

# Verify that the packaged executable exposes an icon through the Windows shell.
# 验证打包后的可执行文件可以通过 Windows Shell 正常读取图标。
Add-Type -AssemblyName System.Drawing
$ExecutablePath = "$ProjectRoot\dist\$AppName\$AppName.exe"
$EmbeddedIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($ExecutablePath)
if ($null -eq $EmbeddedIcon) {
  throw "构建失败：$ExecutablePath 未包含可读取的 EXE 图标"
}
$EmbeddedIcon.Dispose()

Copy-Item "$ProjectRoot\README*.md" "$ProjectRoot\dist\$AppName" -Force
Copy-Item "$ProjectRoot\LICENSES.md" "$ProjectRoot\dist\$AppName\LICENSES.md" -Force
Copy-Item "$ProjectRoot\CHANGELOG.md" "$ProjectRoot\dist\$AppName\CHANGELOG.md" -Force
Copy-Item "$ProjectRoot\docs" "$ProjectRoot\dist\$AppName\docs" -Recurse -Force
Write-Host "构建完成：$ProjectRoot\dist\$AppName"
