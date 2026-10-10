$ErrorActionPreference = 'Stop'
$version = (Select-Xml -Path src/LatchiWatching.App/LatchiWatching.App.csproj -XPath '//Version').Node.InnerText
$root = (Get-Location).Path
New-Item output -ItemType Directory -Force | Out-Null
Copy-Item LICENSE publish/LICENSE.txt
Copy-Item README.md publish/README-LATCHI.md
Copy-Item docs/INSTALL-AR.md publish/INSTALL-AR.md
Copy-Item THIRD-PARTY-NOTICES.md publish/THIRD-PARTY-NOTICES.md
New-Item publish/licenses -ItemType Directory -Force | Out-Null
Copy-Item licenses/* publish/licenses/ -Recurse
$versionInfo = (Get-Item publish/LATCHI-WATCHING.exe).VersionInfo
if ($versionInfo.ProductName -ne 'LATCHI WATCHING' -or $versionInfo.FileVersion -notlike "$version*") { throw 'Renamed EXE/version identity mismatch' }
$zip = Join-Path $root "output/LATCHI-WATCHING-$version-Windows-x64.zip"
Compress-Archive -Path publish/* -DestinationPath $zip -CompressionLevel Optimal
choco install innosetup --version=6.3.1 -y --no-progress
if ($LASTEXITCODE) { throw 'Inno Setup installation failed' }
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
& $iscc "/DMyAppVersion=$version" installer/latchi-watching.iss
if ($LASTEXITCODE) { throw 'Inno Setup compiler failed' }
$setup = Get-ChildItem installer/Output/*.exe | Select-Object -First 1
Copy-Item $setup.FullName output/
# Install to an isolated path; never touch an existing Play or Watching install.
$installed = Join-Path $root 'build/installed test'
$p = Start-Process $setup.FullName -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/DIR="'+$installed+'"'),('/LOG="'+$root+'\evidence\install.log"')) -PassThru -Wait
if ($p.ExitCode -ne 0 -or -not (Test-Path (Join-Path $installed 'LATCHI-WATCHING.exe'))) { throw 'Per-user installation failed' }
# Require exact byte identity of every installed application file.
Get-ChildItem publish -Recurse -File | ForEach-Object {
  $relative = $_.FullName.Substring((Join-Path $root 'publish').Length + 1)
  $copy = Join-Path $installed $relative
  if (-not (Test-Path $copy) -or (Get-FileHash $_.FullName).Hash -ne (Get-FileHash $copy).Hash) { throw "Installed file mismatch: $relative" }
}
$fixture = Join-Path $root 'build/video-fixture'
$installedReport = Join-Path $root 'evidence/installed-ui'
$p = Start-Process (Join-Path $installed 'LATCHI-WATCHING.exe') -ArgumentList @('--self-test',('"'+$fixture+'"'),('"'+$installedReport+'"')) -PassThru
if (-not $p.WaitForExit(110000)) { Stop-Process -Id $p.Id -Force; throw 'Installed runtime timed out' }
if ($p.ExitCode -ne 0) { throw 'Installed runtime/UI test failed' }
$sentinel = Join-Path $installed 'user-added-sentinel.txt'
'preserve user files' | Set-Content $sentinel
$p = Start-Process (Join-Path $installed 'unins000.exe') -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/LOG="'+$root+'\evidence\uninstall.log"')) -PassThru -Wait
if ($p.ExitCode -ne 0 -or (Test-Path (Join-Path $installed 'LATCHI-WATCHING.exe')) -or -not (Test-Path $sentinel)) { throw 'Safe uninstall assertion failed' }
$extract = Join-Path $root 'build/fresh portable'
Expand-Archive $zip $extract
$p = Start-Process (Join-Path $extract 'LATCHI-WATCHING.exe') -ArgumentList @('--self-test',('"'+$fixture+'"'),('"'+$root+'\evidence\portable-ui"')) -PassThru
if (-not $p.WaitForExit(110000)) { Stop-Process -Id $p.Id -Force; throw 'Extracted portable timed out' }
if ($p.ExitCode -ne 0) { throw 'Fresh portable test failed' }
Copy-Item evidence/ui/LATCHI-WATCHING-Home-Windows.png output/
Copy-Item docs/INSTALL-AR.md output/
$ui = Get-Content evidence/ui/ui-report.json -Raw | ConvertFrom-Json
[xml]$trx = Get-Content evidence/core-tests.trx -Raw
$counters = $trx.TestRun.ResultSummary.Counters
if ([int]$counters.failed -ne 0 -or [int]$counters.passed -lt 20) { throw 'Required unit tests not all passed' }
$report = @{version=$version;source_commit=$env:GITHUB_SHA;edition='Windows websites, WPF/WebView2, no cs3';windows_runner='windows-2022';ui=$ui;unit_tests_passed=[int]$counters.passed;installer_install_and_launch_passed=$true;fresh_portable_passed=$true;uninstall_preserved_user_file=$true;code_signed=$false;physical_gpu_audio_tested=$false;all_live_sites_playback_tested=$false}
$report | ConvertTo-Json -Depth 6 | Set-Content output/WINDOWS-VERIFICATION.json -Encoding utf8
& git archive --format=zip --prefix=LATCHI-WATCHING-source/ "--output=output/LATCHI-WATCHING-$version-source.zip" HEAD
if ($LASTEXITCODE) { throw 'Corresponding source archive failed' }
$art = Join-Path $root 'build/artwork'
New-Item $art -ItemType Directory -Force | Out-Null
Copy-Item src/LatchiWatching.App/wwwroot/assets/sources/*.jpg $art/
Copy-Item src/LatchiWatching.App/wwwroot/assets/background.jpg $art/
Copy-Item assets/source-images.json $art/
Compress-Archive -Path "$art/*" -DestinationPath "output/LATCHI-WATCHING-$version-Artwork-3x1.zip"
Get-FileHash output/* -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  $((Split-Path $_.Path -Leaf))" } | Set-Content output/SHA256SUMS.txt -Encoding ascii
Write-Host 'Installer, portable, artwork, source and verification packages are ready.'
