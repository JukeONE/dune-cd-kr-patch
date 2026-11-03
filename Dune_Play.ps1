# Dune CD 런처 - DOSBox Staging 자동 준비 후 Dune CD 실행
$ErrorActionPreference = 'Stop'
$Game   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tools  = Join-Path $Game 'launcher'
$DbDir  = Join-Path $Tools 'dosbox'
$Save   = Join-Path $Game 'SAVE'
$Conf   = Join-Path $Tools 'dune.conf'
$Ver    = 'v0.83.0'
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
$ZipUrl = "https://github.com/dosbox-staging/dosbox-staging/releases/download/$Ver/dosbox-staging-windows-x64-$Ver.zip"

function Find-DosBox {
    $c = @()
    if (Test-Path $DbDir) { $c += Get-ChildItem $DbDir -Recurse -Filter 'dosbox.exe' -ErrorAction SilentlyContinue | ForEach-Object FullName }
    $c += "$env:ProgramFiles\DOSBox Staging\dosbox.exe", "$env:LOCALAPPDATA\Programs\DOSBox Staging\dosbox.exe"
    foreach ($p in $c) { if ($p -and (Test-Path $p)) { return $p } }
    return $null
}

if (-not (Test-Path (Join-Path $Game 'dune.dat'))) {
    Write-Host '[오류] dune.dat 이 없습니다. 이 런처는 Dune CD 폴더 안에 있어야 합니다.' -ForegroundColor Red
    exit 1
}

$dosbox = Find-DosBox
if (-not $dosbox) {
    Write-Host "DOSBox Staging $Ver 을(를) 내려받는 중입니다 (최초 1회, 약 30MB)..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $DbDir | Out-Null
    $zip = Join-Path $Tools 'dosbox.zip'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $ZipUrl -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $DbDir -Force
    Remove-Item $zip -Force
    $dosbox = Find-DosBox
    if (-not $dosbox) { Write-Host '[오류] DOSBox 준비에 실패했습니다.' -ForegroundColor Red; exit 1 }
    Write-Host '완료.' -ForegroundColor Green
}

# 창 크기 설정 (Dune_Window.bat 으로 변경)
$WinFile = Join-Path $Tools 'window.txt'
$Win = 'large'
if (Test-Path $WinFile) { $Win = (Get-Content $WinFile -Raw).Trim() }
$Full = 'false'
if ($Win -eq 'fullscreen') { $Full = 'true'; $Win = 'large' }

$Prog = if (Test-Path (Join-Path $Game 'DNCDKO.EXE')) { 'DNCDKO' } else { 'DNCDPRG' }

# 세이브 폴더 (DOS 안에서는 C:\DUNECD\ 로 보임)
New-Item -ItemType Directory -Force -Path (Join-Path $Save 'DUNECD') | Out-Null

$ConfText = @"
[sdl]
fullscreen = $Full
window_size = $Win

[render]
aspect = true
shader = sharp

[cpu]
core = auto
cpu_cycles = 20000

[mouse]
mouse_capture = seamless

[dosbox]
memsize = 16

[dos]
xms = true
ems = true
umb = true

[sblaster]
sbtype = sbpro2
sbbase = 220
irq = 7
dma = 1
hdma = 5
oplmode = auto

[autoexec]
@echo off
mount c "$Save"
mount d "$Game" -t cdrom -label DUNECD
d:
$Prog AMR ADP220 SBP2227 EMS 386 SAF WRIC:\DUNECD\
exit
"@
[IO.File]::WriteAllText($Conf, $ConfText, (New-Object Text.UTF8Encoding $false))

Write-Host 'Dune CD 를 실행합니다...' -ForegroundColor Cyan
Start-Process -FilePath $dosbox -ArgumentList @('-noprimaryconf', '-nolocalconf', '-conf', "`"$Conf`"") -WorkingDirectory (Split-Path $dosbox)
