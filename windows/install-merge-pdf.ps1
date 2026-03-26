param(
  [string]$RepoBaseUrl = "https://raw.githubusercontent.com/rafael-mansurov/browser-tools/main/windows"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoBaseUrl)) {
  throw "Передай RepoBaseUrl, например: https://raw.githubusercontent.com/OWNER/REPO/main/windows"
}

$installDir = Join-Path $env:LOCALAPPDATA "MergePDF-ContextMenu"
New-Item -Path $installDir -ItemType Directory -Force | Out-Null

$converterScript = Join-Path $installDir "MergeToPDF.ps1"
$uninstallScript = Join-Path $installDir "uninstall-merge-pdf.ps1"

Invoke-WebRequest -Uri ($RepoBaseUrl.TrimEnd('/') + "/MergeToPDF.ps1") -OutFile $converterScript
Invoke-WebRequest -Uri ($RepoBaseUrl.TrimEnd('/') + "/uninstall-merge-pdf.ps1") -OutFile $uninstallScript

$menuKey = "HKCU:\Software\Classes\SystemFileAssociations\.pdf\shell\MergeToPDF"
$commandKey = Join-Path $menuKey "command"

New-Item -Path $menuKey -Force | Out-Null
New-Item -Path $commandKey -Force | Out-Null

Set-ItemProperty -Path $menuKey -Name "(default)" -Value "Merge PDFs"
Set-ItemProperty -Path $menuKey -Name "Icon" -Value "imageres.dll,-2"

$cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $converterScript + '" %*'
Set-ItemProperty -Path $commandKey -Name "(default)" -Value $cmd

Write-Host ""
Write-Host "Готово: пункт Merge PDFs добавлен в контекстное меню." -ForegroundColor Green
Write-Host "Удаление:" -ForegroundColor Yellow
Write-Host 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $uninstallScript + '"'

