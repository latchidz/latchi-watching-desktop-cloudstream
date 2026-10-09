"""Build LATCHI's actual native app, test Windows, and package audited runtimes.
Never substitute a previous executable, suppress a required regression, or publish
from a failing build. Third-party runtime/source bytes are pinned and attributed.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path.cwd()
SOURCE = ROOT / 'source'
sys.path.insert(0, str(SOURCE / 'packaging'))
from release_identity import pe_version_words
from release_runtime import refresh_provider_host
EVIDENCE = ROOT / 'evidence'
OUTPUT = ROOT / 'output'
EVIDENCE.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)
PIN = os.environ['GITHUB_SHA']
VERSION = (SOURCE / 'linux-native/VERSION.txt').read_text().strip()
BASE_HASH = '116b5847c93ea7fc9ba31f2c2882bf26f958fecb5f4e2ed47d1310a3f985de28'
EXE = 'latchi-watching.exe'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(args, cwd=ROOT, log=None, timeout=1200, env=None, check=True):
    print('RUN', args, flush=True)
    command = args if isinstance(args, str) else [str(a) for a in args]
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout, env=env)
    if log:
        (EVIDENCE / log).write_text(result.stdout, encoding='utf-8')
    print(result.stdout[-10000:], flush=True)
    if check and result.returncode:
        raise RuntimeError(f'Required command failed with exit {result.returncode}: {args[0]}')
    return result


def download(url, path):
    print('DOWNLOAD', url, flush=True)
    urllib.request.urlretrieve(url, path)


def build(project, name):
    directory = ROOT / ('build-' + name)
    directory.mkdir(exist_ok=True)
    run(['qmake', project, 'CONFIG+=release', 'CONFIG-=debug_and_release'], directory, name + '-qmake.txt')
    run(['nmake', '/NOLOGO'], directory, name + '-build.txt')
    binaries = list((directory / 'release').glob('*.exe')) or list(directory.glob('*.exe'))
    assert len(binaries) == 1, binaries
    return binaries[0]


assert run(['git', 'rev-parse', 'HEAD'], SOURCE).stdout.strip() == PIN
run(['cl'], log='compiler.txt', check=False)
run([sys.executable, '-m', 'unittest', 'discover', '-s', 'packaging', '-p', 'test_*.py', '-v'], SOURCE, 'packaging-tests.txt')
base = ROOT / 'audited-runtime.zip'
download('https://github.com/dcenhance/cloudstream-pc/releases/download/v0.1.0-preview.3/CloudStream-PC-0.1.0-preview.3-Windows-x64.zip', base)
assert sha(base) == BASE_HASH, 'Audited third-party runtime SHA-256 mismatch'
with zipfile.ZipFile(base) as archive:
    assert archive.testzip() is None
    archive.extractall(ROOT / 'runtime')
runtime = ROOT / 'runtime/CloudStream-PC'
before = {p.relative_to(runtime).as_posix(): sha(p) for p in runtime.rglob('*') if p.is_file()}
old_exe = before['cloudstream.exe']
(runtime / 'cloudstream.exe').unlink()
assert not (runtime / EXE).exists()
deps = ROOT / 'deps'
(deps / 'mpv').mkdir(parents=True)
for header in ['client.h', 'render.h', 'render_gl.h']:
    download('https://raw.githubusercontent.com/mpv-player/mpv/41f6a645068483470267271e1d09966ca3b9f413/include/mpv/' + header, deps / 'mpv' / header)
sdl = deps / 'sdl.zip'
download('https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-devel-2.32.10-VC.zip', sdl)
with zipfile.ZipFile(sdl) as archive:
    assert archive.testzip() is None
    archive.extractall(deps)
import pefile
for dll, lib in [('libmpv-2.dll', 'mpv'), ('SDL2.dll', 'SDL2')]:
    pe = pefile.PE(str(runtime / dll))
    exports = [symbol.name.decode('ascii') for symbol in pe.DIRECTORY_ENTRY_EXPORT.symbols if symbol.name]
    definition = deps / (lib + '.def')
    definition.write_text('LIBRARY ' + dll + '\nEXPORTS\n' + '\n'.join(exports) + '\n')
    run(['lib', '/nologo', '/machine:x64', '/def:' + str(definition), '/out:' + str(deps / (lib + '.lib'))])
os.environ.update(MPV_INCLUDE=deps.as_posix(), SDL2_INCLUDE=(deps / 'SDL2-2.32.10/include').as_posix(),
                  MPV_LIB=(deps / 'mpv.lib').as_posix(), SDL2_LIB=(deps / 'SDL2.lib').as_posix())
exe = build(SOURCE / 'linux-native/cloudstream-linux.pro', 'app')
assert exe.name == EXE
shutil.copy2(exe, runtime / EXE)
assert sha(runtime / EXE) != old_exe
run(['cmd', '/c', str(SOURCE / 'gradlew.bat'), ':provider-host:test', ':provider-host:installDist', '--no-daemon', '--max-workers=2', '-Dorg.gradle.jvmargs=-Xmx2G -Dfile.encoding=UTF-8'],
    SOURCE, 'provider-host-gradle.log', timeout=2400)
changed_provider_files = refresh_provider_host(runtime, SOURCE / 'provider-host/build/install/cloudstream-provider-host', SOURCE / 'packaging/windows-licenses/jvm-provenance.json')

# Adapt only the two POSIX fixture helpers to a native Windows helper, keeping
# production source and test assertions intact. Save the exact adaptation diff.
run(['cl', '/nologo', '/EHsc', '/std:c++17', '/MT', SOURCE / 'packaging/ci/provider-fixture.cpp', '/Fe:' + str(ROOT / 'fixture.exe')])
test = SOURCE / 'linux-native/tests/test_single_window_surfaces.cpp'
text = test.read_text(encoding='utf-8')
start = text.index('        QFile helper(profile.path()')
end = text.index('\n    }', start)
text = text[:start] + '        const auto helper = qEnvironmentVariable("CLOUDSTREAM_TEST_PROVIDER_FIXTURE");\n        QVERIFY(QFileInfo::exists(helper));\n        qputenv("CLOUDSTREAM_PROVIDER_HOST", helper.toUtf8());' + text[end:]
start = text.index('        QFile helper(media.filePath("provider-host"));')
end = text.index('        qputenv("CLOUDSTREAM_EPISODE_VIDEO"', start)
text = text[:start] + '        const auto helper = qEnvironmentVariable("CLOUDSTREAM_TEST_PROVIDER_FIXTURE");\n        QVERIFY(QFileInfo::exists(helper));\n        qputenv("CLOUDSTREAM_PROVIDER_HOST", helper.toUtf8());\n' + text[end:]
test.write_text(text, encoding='utf-8')
(EVIDENCE / 'test-fixture-adaptation.diff').write_text(run(['git', 'diff', '--', 'linux-native/tests/test_single_window_surfaces.cpp'], SOURCE).stdout)
shutil.copy2(Path('C:/Qt/6.8.3/msvc2022_64/bin/Qt6Test.dll'), runtime / 'Qt6Test.dll')
env = os.environ.copy()
env.update(QT_OPENGL='software', QT_QPA_PLATFORM='windows', LATCHI_CI_NULL_AUDIO='1',
           CLOUDSTREAM_TEST_PROVIDER_FIXTURE=str(ROOT / 'fixture.exe'),
           CLOUDSTREAM_TEST_SEARCH_FIXTURE=str(ROOT / 'fixture.exe'),
           CLOUDSTREAM_TEST_EVIDENCE=str(EVIDENCE), PATH=str(runtime) + os.pathsep + os.environ['PATH'])
env.pop('CLOUDSTREAM_UPDATER_LIVE', None)
results = {}
for name in ['latchi-source-hub', 'updater', 'settings-pane', 'single-window-surfaces', 'home-process-result',
             'home-render-yield', 'library-collections', 'search-pagination-model', 'search-pagination-gui',
             'episode-catalog', 'details-presentation', 'player-command', 'repository-manifest',
             'repository-url', 'extension-registry', 'extension-install-batch', 'provider-selection-model',
             'network-request-policy', 'source-catalog', 'mpv-player-widget']:
    binary = build(SOURCE / ('linux-native/tests/' + name + '.pro'), name)
    deployed = runtime / binary.name
    shutil.copy2(binary, deployed)
    result = run([deployed, '-o', str(EVIDENCE / (name + '.xml')) + ',xml', '-o', str(EVIDENCE / (name + '.txt')) + ',txt'],
                 runtime, name + '-console.txt', timeout=360, env=env)
    xml = ET.parse(EVIDENCE / (name + '.xml'))
    results[name] = {'exit_code': result.returncode,
                     'passed': len(xml.findall('.//Incident[@type="pass"]')),
                     'failed': len(xml.findall('.//Incident[@type="fail"]'))}
    assert not results[name]['failed'], name
    deployed.unlink()
(runtime / 'Qt6Test.dll').unlink()

clean = env.copy()
clean['PATH'] = str(runtime) + os.pathsep + str(Path(os.environ['SystemRoot']) / 'System32')
clean.pop('CLOUDSTREAM_PROVIDER_HOST', None)
run([runtime / EXE, '--smoke-test', '--expect-platform', 'windows'], runtime, 'portable-smoke.txt', timeout=45, env=clean)
run([runtime / EXE, '--render-preview', str(EVIDENCE / 'LATCHI-WATCHING-Home.png')], runtime, 'home-screenshot.txt', timeout=60, env=clean)
run([runtime / 'runtime/bin/java.exe', '-version'], runtime, 'java-version.txt', timeout=60, env=clean)
run([runtime / 'ffmpeg.exe', '-version'], runtime, 'ffmpeg-version.txt', timeout=30, env=clean)
run([sys.executable, SOURCE / 'scripts/verify_arabic_source_packages.py', '--runtime', runtime,
     '--workdir', ROOT / 'cs3-probe', '--output', EVIDENCE / 'plugins-report.json', '--probe-catalog', '--require-catalog'],
    ROOT, 'plugins-probe.txt', timeout=900, env=clean)
probe = json.loads((EVIDENCE / 'plugins-report.json').read_text(encoding='utf-8'))

after = {p.relative_to(runtime).as_posix(): sha(p) for p in runtime.rglob('*') if p.is_file()}
assert set(after) == set(before) - {'cloudstream.exe'} | {EXE}
changed_dependencies = sorted(p for p in before if p != 'cloudstream.exe' and before[p] != after[p])
assert changed_dependencies == sorted(changed_provider_files), changed_dependencies
shutil.copy2(ROOT / 'build-app/cloudstream-version.txt', runtime / 'cloudstream-version.txt')
shutil.copy2(SOURCE / 'SOURCES.md', runtime / 'LATCHI-SOURCES-AND-LICENSES.md')
shutil.copy2(SOURCE / 'docs/INSTALL-AR.md', runtime / 'README-LATCHI-AR.md')
assert (runtime / 'cloudstream-version.txt').read_text().strip() == VERSION
info = pefile.PE(str(runtime / EXE))
expected_ms, expected_ls = pe_version_words(VERSION)
assert info.VS_FIXEDFILEINFO[0].FileVersionMS == expected_ms
assert info.VS_FIXEDFILEINFO[0].FileVersionLS == expected_ls

portable = OUTPUT / f'LATCHI-WATCHING-{VERSION}-Windows-x64.zip'
run([sys.executable, SOURCE / 'packaging/build-windows-portable.py', runtime, portable], log='portable-package.txt')
after = {p.relative_to(runtime).as_posix(): sha(p) for p in runtime.rglob('*') if p.is_file()}
(EVIDENCE / 'runtime-manifest.json').write_text(json.dumps(after, indent=2))
with zipfile.ZipFile(portable) as archive:
    assert archive.testzip() is None
    archive.extractall(ROOT / 'fresh extraction')
extracted = ROOT / 'fresh extraction/LATCHI-WATCHING'
for relative, digest in after.items():
    assert sha(extracted / relative) == digest, relative
extracted_env = clean.copy()
extracted_env['PATH'] = str(extracted) + os.pathsep + str(Path(os.environ['SystemRoot']) / 'System32')
run([extracted / EXE, '--smoke-test'], extracted, 'extracted-portable-smoke.txt', timeout=45, env=extracted_env)
if not shutil.which('makensis'):
    run(['choco', 'install', 'nsis', '-y', '--no-progress'])
    os.environ['PATH'] += os.pathsep + 'C:/Program Files (x86)/NSIS'
installer = OUTPUT / f'LATCHI-WATCHING-{VERSION}-Windows-x64-Setup.exe'
run([sys.executable, SOURCE / 'packaging/build-windows-installer.py', runtime, installer, '--version', VERSION], log='installer-package.txt')
installed = ROOT / 'installed test'
run(f'"{installer}" /S /D={installed}', log='install.txt', timeout=180)
for relative, digest in after.items():
    if relative != 'cloudstream-build.json':
        assert sha(installed / relative) == digest, relative
assert json.loads((installed / 'cloudstream-build.json').read_text()) == {'version': VERSION, 'package': 'windows-setup'}
assert json.loads((extracted / 'cloudstream-build.json').read_text()) == {'version': VERSION, 'package': 'windows-zip'}
import winreg
key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\LatchiWatchingCloudStream')
assert winreg.QueryValueEx(key, 'DisplayVersion')[0] == VERSION
assert 'LATCHI WATCHING' in winreg.QueryValueEx(key, 'DisplayName')[0]
key.Close()
run([installed / EXE, '--smoke-test'], installed, 'installed-smoke.txt', timeout=45, env=clean)
sentinel = installed / 'user-added-sentinel.txt'
sentinel.write_text('preserve me')
run(f'"{installed / "Uninstall.exe"}" /S _?={installed}', log='uninstall.txt', timeout=180)
assert not (installed / EXE).exists()
assert sentinel.read_text() == 'preserve me'
try:
    winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Uninstall\LatchiWatchingCloudStream')
except FileNotFoundError:
    pass
else:
    raise AssertionError('Uninstall registry entry remains')

evidence = {'source_commit': PIN, 'version': VERSION, 'base_zip_sha256': BASE_HASH, 'exe_sha256': after[EXE],
            'old_exe_was_removed': True, 'tests': results, 'plugins': probe,
            'installer_lifecycle': {'install_launch_passed': True, 'uninstall_preserved_user_file': True, 'registry_removed': True},
            'windows_runner': 'Windows Server 2022, MSVC 2022, Qt 6.8.3',
            'media_environment': 'software OpenGL, explicit null audio sink, locally generated lawful video',
            'physical_gpu_and_audio_tested': False, 'electron_upgrade_tested': False,
            'live_provider_video_playback_tested': False, 'code_signed': False}
(EVIDENCE / 'build-evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
shutil.copy2(EVIDENCE / 'build-evidence.json', OUTPUT / 'WINDOWS-VERIFICATION.json')
shutil.copy2(EVIDENCE / 'LATCHI-WATCHING-Home.png', OUTPUT / 'LATCHI-WATCHING-Home.png')
shutil.copy2(SOURCE / 'docs/INSTALL-AR.md', OUTPUT / 'INSTALL-AR.md')
run(['git', 'archive', '--format=zip', '--prefix=LATCHI-WATCHING-source/', '--output=' + str(OUTPUT / f'LATCHI-WATCHING-{VERSION}-source.zip'), 'HEAD'], SOURCE, 'source-archive.txt')
(OUTPUT / 'SHA256SUMS.txt').write_text(''.join(sha(path) + '  ' + path.name + '\n' for path in sorted(OUTPUT.iterdir()) if path.is_file() and path.name != 'SHA256SUMS.txt'))
print('LATCHI WINDOWS BUILD, REQUIRED TESTS AND INSTALLER LIFECYCLE PASSED', flush=True)
