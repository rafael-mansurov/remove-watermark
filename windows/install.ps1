param(
  [string]$RepoBaseUrl = "https://raw.githubusercontent.com/rafael-mansurov/remove-watermark/main/windows"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoBaseUrl)) {
  if (Get-Variable base -Scope Script -ErrorAction SilentlyContinue) { $RepoBaseUrl = $base }
  elseif (Get-Variable base -Scope Local -ErrorAction SilentlyContinue) { $RepoBaseUrl = $base }
}

if ([string]::IsNullOrWhiteSpace($RepoBaseUrl)) {
  throw "Передай RepoBaseUrl, например: https://raw.githubusercontent.com/OWNER/REPO/main/windows"
}

$installDir = Join-Path $env:LOCALAPPDATA "WebP-ContextMenu"
New-Item -Path $installDir -ItemType Directory -Force | Out-Null

$converterScript = Join-Path $installDir "ConvertToWebP.ps1"
$uninstallScript = Join-Path $installDir "uninstall.ps1"

Invoke-WebRequest -Uri ($RepoBaseUrl.TrimEnd('/') + "/ConvertToWebP.ps1") -OutFile $converterScript
Invoke-WebRequest -Uri ($RepoBaseUrl.TrimEnd('/') + "/uninstall.ps1") -OutFile $uninstallScript

# Optional dependency install (safe if already installed)
if (-not (Get-Command cwebp -ErrorAction SilentlyContinue)) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    try {
      winget install --id Google.WebP -e --accept-package-agreements --accept-source-agreements | Out-Null
    } catch {
      Write-Host "Не удалось установить WebP через winget. Поставь вручную: скачай libwebp для Windows с https://developers.google.com/speed/webp/download — распакуй bin\cwebp.exe в PATH или в C:\Program Files\libwebp\bin\" -ForegroundColor Yellow
    }
  } else {
    Write-Host "cwebp не найден, а winget недоступен. Скачай libwebp для Windows: https://developers.google.com/speed/webp/download — положи cwebp.exe из bin в PATH или в C:\Program Files\libwebp\bin\" -ForegroundColor Yellow
  }
  if (-not (Get-Command cwebp -ErrorAction SilentlyContinue)) {
    Write-Host "Если cwebp поставился, но не виден — закрой PowerShell и открой снова (обновится PATH)." -ForegroundColor Yellow
  }
}

$menuKey = "HKCU:\Software\Classes\SystemFileAssociations\image\shell\ConvertToWebP"
$commandKey = Join-Path $menuKey "command"

New-Item -Path $menuKey -Force | Out-Null
New-Item -Path $commandKey -Force | Out-Null

Set-ItemProperty -Path $menuKey -Name "(default)" -Value "Convert to WebP"
Set-ItemProperty -Path $menuKey -Name "Icon" -Value "imageres.dll,-5302"

$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $converterScript + '" %*'
Set-ItemProperty -Path $commandKey -Name "(default)" -Value $cmd

Write-Host ""
Write-Host "Готово: пункт Convert to WebP добавлен в контекстное меню." -ForegroundColor Green
Write-Host "Удаление: powershell -NoProfile -ExecutionPolicy Bypass -File `"$uninstallScript`""
