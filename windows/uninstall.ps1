$ErrorActionPreference = "Stop"

$menuKey = "HKCU:\Software\Classes\SystemFileAssociations\image\shell\ConvertToWebP"
if (Test-Path $menuKey) {
  Remove-Item -Path $menuKey -Recurse -Force
  Write-Host "Пункт Convert to WebP удален из контекстного меню." -ForegroundColor Green
} else {
  Write-Host "Пункт меню не найден." -ForegroundColor Yellow
}
