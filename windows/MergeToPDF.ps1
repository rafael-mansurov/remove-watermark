param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$InputPaths
)

$ErrorActionPreference = "Stop"

function Resolve-QpdfPath {
  $cmd = Get-Command qpdf -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }

  $candidates = @(
    "$env:ProgramFiles\\qpdf\\bin\\qpdf.exe",
    "${env:ProgramFiles(x86)}\\qpdf\\bin\\qpdf.exe",
    "C:\\Program Files\\qpdf\\bin\\qpdf.exe"
  )
  foreach ($p in $candidates) {
    if ([string]::IsNullOrWhiteSpace($p)) { continue }
    if (Test-Path -LiteralPath $p) { return $p }
  }
  return $null
}

function Get-FirstNumber {
  param([string]$Name)
  if ([string]::IsNullOrWhiteSpace($Name)) { return $null }
  $m = [regex]::Match($Name, "(\d+)")
  if (-not $m.Success) { return $null }
  $val = 0
  if ([int]::TryParse($m.Groups[1].Value, [ref]$val)) { return $val }
  return $null
}

$qpdf = Resolve-QpdfPath
if (-not $qpdf) {
  Write-Host "Не найден qpdf.exe. Установи qpdf и попробуй снова." -ForegroundColor Red
  exit 1
}

if (-not $InputPaths -or $InputPaths.Count -eq 0) {
  Write-Host "Передай PDF через контекстное меню Explorer." -ForegroundColor Yellow
  exit 1
}

$pdfs = @()
for ($i = 0; $i -lt $InputPaths.Count; $i++) {
  $p = $InputPaths[$i]
  if ([string]::IsNullOrWhiteSpace($p)) { continue }
  if (-not (Test-Path -LiteralPath $p)) { continue }
  $ext = [System.IO.Path]::GetExtension($p).ToLowerInvariant()
  if ($ext -ne ".pdf") { continue }
  $pdfs += $p
}

if ($pdfs.Count -lt 2) {
  Write-Host "Выбери хотя бы 2 PDF." -ForegroundColor Yellow
  exit 0
}

# stable sort: сначала числа, потом нечисловые, внутри числовых по числу, внутри одинаковых по исходному индексу
$items = @()
for ($idx = 0; $idx -lt $pdfs.Count; $idx++) {
  $full = $pdfs[$idx]
  $nameNoExt = [System.IO.Path]::GetFileNameWithoutExtension($full)
  $num = Get-FirstNumber -Name $nameNoExt
  $items += [pscustomobject]@{
    Idx = $idx
    Path = $full
    Num = $num
  }
}

$sortedItems = $items | Sort-Object `
  @{ Expression = { $_.Num -eq $null } ; Ascending = $true }, `
  @{ Expression = { if ($_.Num -eq $null) { 0 } else { $_.Num } } ; Ascending = $true }, `
  @{ Expression = { $_.Idx } ; Ascending = $true }

$sortedPaths = @()
foreach ($it in $sortedItems) { $sortedPaths += $it.Path }

$first = [System.IO.Path]::GetFileNameWithoutExtension($sortedPaths[0])
$outdir = Join-Path ([Environment]::GetFolderPath("Desktop")) "Merged-PDF"
New-Item -Path $outdir -ItemType Directory -Force | Out-Null
$out = Join-Path $outdir ($first + "-merged.pdf")

Write-Host "Склеиваю: $($sortedPaths.Count) PDF -> $out"

$pageArgs = @()
foreach ($p in $sortedPaths) { $pageArgs += $p }

& $qpdf --empty --pages $pageArgs -- $out | Out-Null

if (Test-Path -LiteralPath $out) {
  Write-Host "Готово: $out" -ForegroundColor Green
  Start-Process explorer.exe $outdir
} else {
  Write-Host "Не удалось создать файл." -ForegroundColor Red
}

Read-Host "Нажми Enter для выхода"

