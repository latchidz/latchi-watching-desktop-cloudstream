#!/usr/bin/env python3
"""Package an already deployed Windows runtime using NSIS (Linux or Windows)."""
import argparse
import pathlib
import subprocess
import tempfile
from release_identity import identity, release_version, require_build_version


def nsis_quote(value):
    value = str(value)
    if '\n' in value or '\r' in value:
        raise ValueError('Newlines are not allowed in package paths')
    return value.replace('$', '$$').replace('"', '$\\"')


def nsis_file_pattern(runtime):
    """File directives need host-native separators, including the wildcard."""
    return nsis_quote(runtime / '*')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=pathlib.Path)
    parser.add_argument('output', type=pathlib.Path)
    parser.add_argument('--version', default=release_version())
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    output = args.output.resolve()
    marker = identity("windows-setup", args.version).strip()
    require_build_version(runtime / "cloudstream-version.txt")
    for required in ('latchi-watching.exe', 'runtime/bin/java.exe', 'platforms/qwindows.dll'):
        if not (runtime / required).is_file():
            parser.error(f'Missing runtime file: {required}')
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = sorted(runtime.rglob('*'))
    if any(p.is_symlink() for p in paths):
        parser.error('Runtime must not contain symlinks')
    files = [p for p in paths if p.is_file()]
    # Explicit deletes preserve files added by the user after installation.
    deletes = '\n'.join('Delete "$INSTDIR\\' + nsis_quote(str(p.relative_to(runtime)).replace('/', '\\')) + '"' for p in files)
    dirs = sorted((p for p in paths if p.is_dir()), key=lambda p: len(p.parts), reverse=True)
    removes = '\n'.join('RMDir "$INSTDIR\\' + nsis_quote(str(p.relative_to(runtime)).replace('/', '\\')) + '"' for p in dirs)
    script = '''Unicode true
!include "MUI2.nsh"
!include "x64.nsh"
Name "LATCHI WATCHING CloudStream"
VIProductVersion "@NUMERIC_VERSION@.0"
VIAddVersionKey /LANG=1033 "ProductName" "LATCHI WATCHING CloudStream"
VIAddVersionKey /LANG=1033 "CompanyName" "LATCHI"
VIAddVersionKey /LANG=1033 "FileDescription" "LATCHI WATCHING CloudStream per-user installer"
VIAddVersionKey /LANG=1033 "FileVersion" "@VERSION@"
VIAddVersionKey /LANG=1033 "LegalCopyright" "CloudStream contributors; GPL v3"
!define MUI_ICON "@ICON@"
!define MUI_UNICON "@ICON@"
OutFile "@OUTPUT@"
InstallDir "$LOCALAPPDATA\\Programs\\LATCHI WATCHING CloudStream"
RequestExecutionLevel user
SetCompressor /SOLID lzma
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "LATCHI WATCHING CloudStream requires 64-bit Windows."
    Abort
  ${EndIf}
FunctionEnd
Section "LATCHI WATCHING CloudStream"
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "@FILE_PATTERN@"
  FileOpen $0 "$INSTDIR\\cloudstream-build.json" w
  FileWrite $0 "@IDENTITY@"
  FileClose $0
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\\LATCHI WATCHING CloudStream"
  CreateShortcut "$SMPROGRAMS\\LATCHI WATCHING CloudStream\\LATCHI WATCHING CloudStream.lnk" "$INSTDIR\\latchi-watching.exe"
  CreateShortcut "$DESKTOP\\LATCHI WATCHING CloudStream.lnk" "$INSTDIR\\latchi-watching.exe"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LatchiWatchingCloudStream" "DisplayName" "LATCHI WATCHING CloudStream"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LatchiWatchingCloudStream" "DisplayVersion" "@VERSION@"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LatchiWatchingCloudStream" "Publisher" "LATCHI"
  WriteRegStr HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LatchiWatchingCloudStream" "UninstallString" '$\\"$INSTDIR\\Uninstall.exe$\\"'
  WriteRegDWORD HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LatchiWatchingCloudStream" "NoModify" 1
  WriteRegDWORD HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LatchiWatchingCloudStream" "NoRepair" 1
SectionEnd
Section "Uninstall"
  SetShellVarContext current
@DELETES@
  Delete "$INSTDIR\\Uninstall.exe"
@REMOVES@
  RMDir "$INSTDIR"
  Delete "$DESKTOP\\LATCHI WATCHING CloudStream.lnk"
  Delete "$SMPROGRAMS\\LATCHI WATCHING CloudStream\\LATCHI WATCHING CloudStream.lnk"
  RMDir "$SMPROGRAMS\\LATCHI WATCHING CloudStream"
  DeleteRegKey HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\LatchiWatchingCloudStream"
SectionEnd
'''
    for key, value in {'NUMERIC_VERSION': args.version.partition('-')[0], 'IDENTITY': nsis_quote(marker), 'OUTPUT': nsis_quote(output), 'FILE_PATTERN': nsis_file_pattern(runtime), 'ICON': nsis_quote(pathlib.Path(__file__).with_name('latchi-watching.ico').resolve()), 'VERSION': nsis_quote(args.version), 'DELETES': deletes, 'REMOVES': removes}.items():
        script = script.replace('@' + key + '@', value)
    with tempfile.TemporaryDirectory(prefix='cloudstream-nsis-') as tmp:
        path = pathlib.Path(tmp) / 'installer.nsi'
        path.write_text(script, encoding='utf-8')
        subprocess.run(['makensis', '-V2', str(path)], check=True)
    print(output)


if __name__ == '__main__':
    main()
