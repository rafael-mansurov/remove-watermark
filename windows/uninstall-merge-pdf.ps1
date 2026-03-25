$ErrorActionPreference = "Stop"

$menuKey = "HKCU:\Software\Classes\SystemFileAssociations\.pdf\shell\MergeToPDF"
if (Test-Path $menuKey) {
  Remove-Item -Path $menuKey -Recurse -Force
  Write-Host "Пункт Merge PDFs удален из контекстного меню." -ForegroundColor Green
} else {
  Write-Host "Пункт меню не найден." -ForegroundColor Yellow
}

