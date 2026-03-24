param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$InputPaths
)

$ErrorActionPreference = "Stop"

function Resolve-CwebpPath {
  $cmd = Get-Command cwebp -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }

  $candidates = @(
    "$env:ProgramFiles\libwebp\bin\cwebp.exe",
    "$env:ProgramFiles\WebP\bin\cwebp.exe",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Google.WebP_Microsoft.Winget.Source_8wekyb3d8bbwe\cwebp.exe"
  )
  foreach ($p in $candidates) {
    if (Test-Path $p) { return $p }
  }
  return $null
}

function Get-Quality {
  while ($true) {
    $raw = Read-Host "Качество WebP (1-100, Enter = 80)"
    if ([string]::IsNullOrWhiteSpace($raw)) { return 80 }
    $q = 0
    if ([int]::TryParse($raw, [ref]$q) -and $q -ge 1 -and $q -le 100) {
      return $q
    }
    Write-Host "Нужно число от 1 до 100." -ForegroundColor Yellow
  }
}

$cwebp = Resolve-CwebpPath
if (-not $cwebp) {
  Write-Host "Не найден cwebp.exe. Установи WebP и добавь cwebp в PATH." -ForegroundColor Red
  Read-Host "Нажми Enter для выхода"
  exit 1
}

if (-not $InputPaths -or $InputPaths.Count -eq 0) {
  Write-Host "Передай фото через контекстное меню Explorer." -ForegroundColor Yellow
  Read-Host "Нажми Enter для выхода"
  exit 1
}

$quality = Get-Quality
$outDir = Join-Path ([Environment]::GetFolderPath("Desktop")) "WebP"
New-Item -Path $outDir -ItemType Directory -Force | Out-Null

$allowed = @(".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")
$converted = 0

foreach ($rawPath in $InputPaths) {
  if ([string]::IsNullOrWhiteSpace($rawPath)) { continue }
  if (-not (Test-Path -LiteralPath $rawPath)) { continue }

  $item = Get-Item -LiteralPath $rawPath -ErrorAction SilentlyContinue
  if (-not $item -or $item.PSIsContainer) { continue }

  $ext = [IO.Path]::GetExtension($item.Name).ToLowerInvariant()
  if ($allowed -notcontains $ext) { continue }

  $base = [IO.Path]::GetFileNameWithoutExtension($item.Name)
  $dst = Join-Path $outDir ($base + ".webp")

  & $cwebp -q $quality -- "$($item.FullName)" -o "$dst" | Out-Null
  if ($LASTEXITCODE -eq 0) {
    $converted++
    Write-Host "OK: $($item.Name) -> $([IO.Path]::GetFileName($dst))"
  } else {
    Write-Host "Ошибка: $($item.Name)" -ForegroundColor Red
  }
}

if ($converted -gt 0) {
  Write-Host ""
  Write-Host "Готово. Сконвертировано: $converted. Папка: $outDir" -ForegroundColor Green
  Start-Process explorer.exe $outDir
} else {
  Write-Host "Подходящие файлы не найдены или конвертация не удалась." -ForegroundColor Yellow
}

Read-Host "Нажми Enter для выхода"
