# Dune 창 크기 설정
$Game  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tools = Join-Path $Game 'launcher'
New-Item -ItemType Directory -Force -Path $Tools | Out-Null
$File  = Join-Path $Tools 'window.txt'
$cur = if (Test-Path $File) { (Get-Content $File -Raw).Trim() } else { 'large' }

$opts = @(
    @('640x480',    '640 x 480'),
    @('800x600',    '800 x 600'),
    @('1024x768',   '1024 x 768'),
    @('1280x960',   '1280 x 960'),
    @('medium',     '화면 크기에 맞춰 중간'),
    @('large',      '화면 크기에 맞춰 크게 (기본값)'),
    @('fullscreen', '전체화면')
)
Write-Host ''
Write-Host '  Dune 창 크기 설정' -ForegroundColor Cyan
Write-Host "  (현재: $cur)"
Write-Host ''
for ($i = 0; $i -lt $opts.Count; $i++) { Write-Host ("  {0}. {1}" -f ($i + 1), $opts[$i][1]) }
Write-Host ''
$sel = Read-Host '  번호를 입력하세요'
$n = 0
if (-not [int]::TryParse($sel, [ref]$n) -or $n -lt 1 -or $n -gt $opts.Count) {
    Write-Host '  잘못된 번호입니다. 바뀐 것은 없습니다.' -ForegroundColor Yellow
    exit 1
}
[IO.File]::WriteAllText($File, $opts[$n - 1][0])
Write-Host ("  '{0}' 으로 저장했습니다. Dune_Play.bat 으로 실행하세요." -f $opts[$n - 1][1]) -ForegroundColor Green
Write-Host '  (윈도우 배율이 100%가 아니면 창이 그 배율만큼 더 크게 보일 수 있습니다.)'
