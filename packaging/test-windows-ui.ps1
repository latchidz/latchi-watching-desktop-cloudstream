$ErrorActionPreference = 'Stop'
New-Item evidence -ItemType Directory -Force | Out-Null
$root = (Get-Location).Path
$fixture = Join-Path $root 'build/video-fixture'
$report = Join-Path $root 'evidence/ui'
New-Item $fixture -ItemType Directory -Force | Out-Null
New-Item $report -ItemType Directory -Force | Out-Null
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) { $env:Path += ';C:\ProgramData\chocolatey\bin'; $ffmpeg = Get-Command ffmpeg -ErrorAction Stop }
& $ffmpeg.Source -loglevel error -y -f lavfi -i 'testsrc2=size=640x360:rate=24' -t 5 -an -c:v libvpx -b:v 900k (Join-Path $fixture 'test.webm')
if ($LASTEXITCODE) { throw 'Lawful video generation failed' }
@'
<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;height:100%;background:#05070c}video{width:100%;height:100%;object-fit:contain}</style></head><body><video autoplay muted loop playsinline controls src="test.webm"></video></body></html>
'@ | Set-Content (Join-Path $fixture 'index.html') -Encoding UTF8
python -c "from pathlib import Path;from PIL import Image;p=Path('publish/wwwroot/assets');a=list((p/'sources').glob('*.jpg'))+[p/'background.jpg'];assert len(a)==9;assert all(Image.open(x).size==(1800,600) for x in a);print('All nine images: 1800x600, exact 3:1.')"
if ($LASTEXITCODE) { throw 'Artwork integrity assertion failed' }
$p = Start-Process (Join-Path $root 'publish/LATCHI-WATCHING.exe') -ArgumentList @('--self-test',('"'+$fixture+'"'),('"'+$report+'"')) -PassThru
if (-not $p.WaitForExit(110000)) { Stop-Process -Id $p.Id -Force; throw 'Windows UI self-test timed out' }
$exit = $p.ExitCode
if (Test-Path (Join-Path $report 'ui-report.json')) { Get-Content (Join-Path $report 'ui-report.json') }
if ($exit -ne 0) { throw "Windows UI/media self-test failed: $exit" }
$r = Get-Content (Join-Path $report 'ui-report.json') -Raw | ConvertFrom-Json
if (-not $r.passed) { throw 'Required UI report is not successful' }
Write-Host 'Required real Windows UI and locally generated video tests passed.'
