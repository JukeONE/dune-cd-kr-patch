# Dune CD 한글패치 설치/복원
param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$Here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Game  = Split-Path -Parent $Here
$Dat   = Join-Path $Game 'dune.dat'
$Bak   = Join-Path $Here 'dune_dat_index.bak'
$OrigX = Join-Path $Game 'dncdprg.exe'
$KoExe = Join-Path $Game 'DNCDKO.EXE'

function Get-Md5([byte[]]$b) {
    $m = [Security.Cryptography.MD5]::Create()
    -join ($m.ComputeHash($b) | ForEach-Object { $_.ToString('x2') })
}
function Apply-Patch([byte[]]$orig, $p, [string]$what) {
    if ((Get-Md5 $orig) -ne $p.md5) { throw "$what 원본이 지원하는 버전과 다릅니다. Dune CD 버전 원본 파일인지 확인하세요." }
    $new = New-Object byte[] ([int]$p.newSize)
    [Array]::Copy($orig, $new, [Math]::Min($orig.Length, $new.Length))
    foreach ($c in $p.chunks) {
        $d = [Convert]::FromBase64String($c.d)
        [Array]::Copy($d, 0, $new, [int]$c.o, $d.Length)
    }
    return ,$new
}
function Restore-Dat {
    if (-not (Test-Path $Bak)) { return }
    $b = [IO.File]::ReadAllBytes($Bak)
    $len = [BitConverter]::ToInt64($b, 0)
    $fs = [IO.File]::Open($Dat, 'Open', 'ReadWrite')
    try { $fs.Position = 0; $fs.Write($b, 8, $b.Length - 8); $fs.SetLength($len) } finally { $fs.Close() }
    Remove-Item $Bak -Force
}

if (-not (Test-Path $Dat)) { throw "dune.dat 을 찾을 수 없습니다: $Dat`n이 폴더를 Dune CD 게임 폴더 안에 넣어 주세요." }

if ($Restore) {
    Restore-Dat
    if (Test-Path $KoExe) { Remove-Item $KoExe -Force }
    Write-Host '원본으로 복원했습니다.' -ForegroundColor Green
    exit 0
}

$patch = Get-Content (Join-Path $Here 'patch.json') -Raw | ConvertFrom-Json

# 1) 실행 파일: 원본 dncdprg.exe 에 패치를 적용해 DNCDKO.EXE 생성
if (-not (Test-Path $OrigX)) { throw "dncdprg.exe 를 찾을 수 없습니다." }
$exe = Apply-Patch ([IO.File]::ReadAllBytes($OrigX)) $patch.exe 'dncdprg.exe'

# 2) dune.dat: 깨끗한 상태로 되돌린 뒤 한글 파일을 덧붙이고 인덱스만 교체
Restore-Dat
if ((Get-Item $Dat).IsReadOnly) { Set-ItemProperty $Dat -Name IsReadOnly -Value $false }
$fs = [IO.File]::Open($Dat, 'Open', 'ReadWrite')
try {
    $hdr = New-Object byte[] 2; [void]$fs.Read($hdr, 0, 2)
    $count = [BitConverter]::ToUInt16($hdr, 0)
    $idxLen = 2 + $count * 25
    $idx = New-Object byte[] $idxLen
    $fs.Position = 0; [void]$fs.Read($idx, 0, $idxLen)
    $origLen = $fs.Length
    $bk = New-Object byte[] (8 + $idxLen)
    [BitConverter]::GetBytes([int64]$origLen).CopyTo($bk, 0); $idx.CopyTo($bk, 8)
    [IO.File]::WriteAllBytes($Bak, $bk)

    $names = @{}
    for ($i = 0; $i -lt $count; $i++) {
        $o = 2 + $i * 25
        $n = [Text.Encoding]::ASCII.GetString($idx, $o, 16).Split([char]0)[0]
        if ($n) { $names[$n.ToUpper()] = $o }
    }
    $items = @()
    foreach ($f in Get-ChildItem (Join-Path $Here 'files') -File) {
        $items += ,@($f.Name.ToUpper(), [IO.File]::ReadAllBytes($f.FullName))
    }
    foreach ($prop in $patch.dat.PSObject.Properties) {
        $o = $names[$prop.Name.ToUpper()]
        if ($null -eq $o) { throw "dune.dat 에 $($prop.Name) 이(가) 없습니다." }
        $size = [BitConverter]::ToUInt32($idx, $o + 16); $off = [BitConverter]::ToUInt32($idx, $o + 20)
        $orig = New-Object byte[] $size
        $fs.Position = $off; [void]$fs.Read($orig, 0, $size)
        $items += ,@($prop.Name.ToUpper(), (Apply-Patch $orig $prop.Value $prop.Name))
    }
    $pos = $origLen
    foreach ($it in $items) {
        $o = $names[$it[0]]
        if ($null -eq $o) { throw "dune.dat 인덱스에 없는 파일: $($it[0])" }
        $data = $it[1]
        $pos = [int64]([math]::Ceiling($pos / 2048) * 2048)
        $fs.Position = $pos; $fs.Write($data, 0, $data.Length)
        [BitConverter]::GetBytes([uint32]$data.Length).CopyTo($idx, $o + 16)
        [BitConverter]::GetBytes([uint32]$pos).CopyTo($idx, $o + 20)
        $pos += $data.Length
        Write-Host "  적용: $($it[0])"
    }
    $fs.Position = 0; $fs.Write($idx, 0, $idxLen)
} finally { $fs.Close() }

[IO.File]::WriteAllBytes($KoExe, $exe)
Write-Host '한글패치를 설치했습니다. Dune_Play.bat 으로 실행하세요.' -ForegroundColor Green
