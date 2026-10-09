#!/usr/bin/env python3
"""Publish a verified, GPL-compliant Windows release without replacing old assets.
The temporary PAT is supplied as an Actions secret only to this publisher, never
stored in source files or sent to binary/source download servers.
"""
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

SOURCE_REPO = 'latchidz/latchi-watching-desktop-cloudstream'
RELEASE_REPO = 'latchidz/LATCHI-RELEASES'
ROOT = Path.cwd()
OUTPUT = ROOT / 'output'
TOKEN = os.environ.get('LATCHI_RELEASE_TOKEN', '')
COMMIT = os.environ['GITHUB_SHA']
VERSION = (ROOT / 'linux-native/VERSION.txt').read_text().strip()
TAG = 'watching-cloudstream-v' + VERSION
ARCHIVE_BASE = 'https://github.com/dcenhance/cloudstream-pc/releases/download/v0.1.0-preview.3/'
DEPENDENCY_SOURCES = {
    'CloudStream-PC-0.1.0-preview.3-Common-sources.tar': 'fbf1d2efa8e8debf600e298a543ef3d9851665d303291a0336b36b0295e1a903',
    'CloudStream-Windows-MSYS2-metadata.tar': '38d982f840ff44eeaba34fc88430b044c130034a557ced9e1aaf50920f62032b',
    'CloudStream-Windows-MSYS2-sources.tar': '64e98910a0539b6490c3c1a8583dc425ac7a33b49ac70b25625dffa4ab2af324',
    'CloudStream-Windows-MSYS2-supplementary.tar': '25933a2c41e7faac1ad76355bb8f12913db6ef865c5ad7db3de91f4c15749e49',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def api(method, path, payload=None, missing_ok=False):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {'Authorization': 'Bearer ' + TOKEN, 'Accept': 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'LATCHI-native-release', 'Content-Type': 'application/json'}
    request = urllib.request.Request('https://api.github.com' + path, headers=headers, data=body, method=method)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        if error.code == 404 and missing_ok:
            return None
        raise RuntimeError(f'GitHub {method} failed with HTTP {error.code}: {path}') from None


def upload(release, path):
    digest = 'sha256:' + sha(path)
    existing = next((asset for asset in release['assets'] if asset['name'] == path.name), None)
    if existing:
        if existing['size'] != path.stat().st_size or existing.get('digest') != digest:
            raise RuntimeError('Refusing to overwrite a different existing release asset: ' + path.name)
        print('VERIFIED EXISTING', path.name, flush=True)
        return existing
    connection = http.client.HTTPSConnection('uploads.github.com', timeout=1200)
    target = f'/repos/{RELEASE_REPO}/releases/{release["id"]}/assets?name=' + urllib.parse.quote(path.name, safe='')
    connection.putrequest('POST', target)
    for key, value in {'Authorization': 'Bearer ' + TOKEN, 'Accept': 'application/vnd.github+json',
                       'User-Agent': 'LATCHI-native-release', 'Content-Type': 'application/octet-stream',
                       'Content-Length': str(path.stat().st_size)}.items():
        connection.putheader(key, value)
    connection.endheaders()
    print('UPLOAD', path.name, path.stat().st_size, 'bytes', flush=True)
    with path.open('rb') as stream:
        while block := stream.read(2 * 1024 * 1024):
            connection.send(block)
    response = connection.getresponse()
    raw = response.read()
    connection.close()
    if response.status != 201:
        raise RuntimeError(f'Asset upload failed with HTTP {response.status}: {path.name}')
    asset = json.loads(raw)
    if asset.get('digest') != digest or asset['size'] != path.stat().st_size:
        raise RuntimeError('GitHub asset digest/size does not match uploaded bytes: ' + path.name)
    return asset


def main():
    if not TOKEN:
        raise RuntimeError('Temporary release secret is missing; no release was published.')
    if not re.fullmatch(r'[0-9a-f]{40}', COMMIT) or not re.fullmatch(r'\d+\.\d+\.\d+', VERSION):
        raise RuntimeError('Invalid immutable release identity')
    evidence = json.loads((OUTPUT / 'WINDOWS-VERIFICATION.json').read_text(encoding='utf-8'))
    assert evidence['source_commit'] == COMMIT and evidence['version'] == VERSION
    assert evidence['old_exe_was_removed'] and all(t['exit_code'] == 0 and t['failed'] == 0 for t in evidence['tests'].values())
    plugins = evidence['plugins']
    assert plugins['registration_passed'] == 8 and plugins['catalogs_with_items'] > 0 and plugins['details_passed'] > 0
    assert evidence['installer_lifecycle']['install_launch_passed'] and evidence['installer_lifecycle']['uninstall_preserved_user_file']
    required = [f'LATCHI-WATCHING-{VERSION}-Windows-x64-Setup.exe', f'LATCHI-WATCHING-{VERSION}-Windows-x64.zip', f'LATCHI-WATCHING-{VERSION}-source.zip']
    assert all((OUTPUT / name).is_file() for name in required)
    # Download corresponding source without credentials; verify the original pins.
    for name, expected in DEPENDENCY_SOURCES.items():
        path = OUTPUT / name
        if not path.exists():
            print('FETCH CORRESPONDING SOURCE', name, flush=True)
            urllib.request.urlretrieve(ARCHIVE_BASE + name, path)
        assert sha(path) == expected, 'Third-party source archive hash mismatch: ' + name
    (OUTPUT / 'SOURCES-AND-LICENSES.md').write_bytes((ROOT / 'SOURCES.md').read_bytes())
    paths = sorted(path for path in OUTPUT.iterdir() if path.is_file() and path.name != 'SHA256SUMS.txt')
    (OUTPUT / 'SHA256SUMS.txt').write_text(''.join(sha(path) + '  ' + path.name + '\n' for path in paths))
    paths.append(OUTPUT / 'SHA256SUMS.txt')
    marker = '<!-- LATCHI_SOURCE_COMMIT=' + COMMIT + ' -->'
    passed = sum(test['passed'] for test in evidence['tests'].values())
    lines = [
        f'# LATCHI WATCHING {VERSION} — Windows x64', '',
        'نسخة Qt/JVM أصلية من CloudStream، وليست MSI تجريبيًا أو متصفح مواقع.',
        'الرئيسية تبدأ بالمصادر الثمانية وبطاقات RTL بنسبة 3:1. الإضافات تحتاج موافقة صريحة وتحققًا من البصمة.', '',
        f'## نتائج البناء من `{COMMIT}`',
        f'- {len(evidence["tests"])} مجموعة اختبارات Windows مطلوبة؛ {passed} نتيجة نجاح، دون إخفاقات.',
        '- Java 17 provider-host: unit tests, conversion and registration of all eight real `.cs3` packages.',
        '- Generated lawful local video: decode/render/seek, with software OpenGL and an explicit null audio sink.',
        '- Fresh portable extraction and per-user installer launch/uninstall passed; user-added files preserved.',
        f'- Real provider catalogs returned items for {plugins["catalogs_with_items"]}/8 sources; details succeeded for {plugins["details_passed"]}/8.', '',
        '| المصدر | تسجيل JVM | عناوين الكتالوغ وقت الاختبار | تفاصيل |',
        '|---|---:|---:|---:|',
    ]
    for package in plugins['packages']:
        lines.append(f'| `{package["id"]}` | {"نجح" if package["registered"] else "فشل"} | {package["catalog_items"]} | {"نجح" if package["details"] else "غير مثبت"} |')
    lines += ['', '## حدود صريحة',
              '- لا ندّعي التشغيل الحي للفيديو من جميع مواقع المصادر؛ فحص الكتالوغ والتفاصيل ليس اختبار تشغيل فيديو حي.',
              '- لا يوجد اختبار GPU أو جهاز صوت حقيقي أو وحدات تحكم. الخادم يستخدم تصييرًا برمجيًا ومخرج صوت افتراضيًا.',
              '- هذا تثبيت مستقل عن Electron 0.1.2؛ لم نختبر ترقية Electron أو نقل بياناته.',
              '- المثبّت غير موقّع. تحقق من SHA256SUMS ولا تعطّل حماية Windows.',
              '- مواقع المصادر قد تمنع شبكة الخادم أو تتغير أو تتوقف. راجع WINDOWS-VERIFICATION.json للأخطاء الفعلية.', '',
              '## الملفات', '- Setup: مثبّت Windows للحساب الحالي.', '- ZIP: فك الحزمة كاملة ثم شغّل `latchi-watching.exe`.',
              '- Source ZIP: المصدر المطابق GPLv3، والتراخيص محفوظة.',
              '- Common/MSYS2 source archives: مصادر واعتمادات الطرف الثالث، لا تحتاجها لتشغيل التطبيق.',
              f'- [المصدر المطابق](https://github.com/{SOURCE_REPO}/tree/{TAG})',
              '- INSTALL-AR.md: دليل عربي، WINDOWS-VERIFICATION.json: الاختبارات، SHA256SUMS.txt: البصمات.', '', marker]
    body = '\n'.join(lines)
    source_ref = api('GET', f'/repos/{SOURCE_REPO}/git/ref/tags/{TAG}', missing_ok=True)
    if source_ref:
        if source_ref['object']['sha'] != COMMIT:
            raise RuntimeError('Source tag already points to another commit; use a new version, never replace a tag.')
    else:
        api('POST', f'/repos/{SOURCE_REPO}/git/refs', {'ref': 'refs/tags/' + TAG, 'sha': COMMIT})
    release = api('GET', f'/repos/{RELEASE_REPO}/releases/tags/{TAG}', missing_ok=True)
    if release:
        if marker not in release.get('body', ''):
            raise RuntimeError('Release tag belongs to another source revision; refusing to overwrite it.')
    else:
        release = api('POST', f'/repos/{RELEASE_REPO}/releases', {
            'tag_name': TAG, 'target_commitish': 'main', 'name': 'LATCHI WATCHING ' + VERSION + ' — native CloudStream',
            'body': body, 'draft': True, 'prerelease': False, 'make_latest': 'false'})
    if not release['draft']:
        for path in paths:
            existing = next((asset for asset in release['assets'] if asset['name'] == path.name), None)
            if not existing or existing.get('digest') != 'sha256:' + sha(path):
                raise RuntimeError('Existing public release is immutable and differs from this output.')
    else:
        for path in paths:
            upload(release, path)
        release = api('PATCH', f'/repos/{RELEASE_REPO}/releases/{release["id"]}', {'draft': False, 'prerelease': False, 'make_latest': 'false', 'body': body})
    release = api('GET', f'/repos/{RELEASE_REPO}/releases/{release["id"]}')
    assets = {asset['name']: asset for asset in release['assets']}
    installer = assets[required[0]]
    with urllib.request.urlopen(urllib.request.Request(installer['browser_download_url'], method='HEAD', headers={'User-Agent':'LATCHI-native-release'}), timeout=90) as response:
        assert response.status == 200
    result = {'source_commit': COMMIT, 'version': VERSION, 'release': release['html_url'],
              'installer': installer['browser_download_url'], 'installer_sha256': installer['digest'],
              'portable': assets[required[1]]['browser_download_url'], 'source': assets[required[2]]['browser_download_url'],
              'checksums': assets['SHA256SUMS.txt']['browser_download_url'],
              'verification': assets['WINDOWS-VERIFICATION.json']['browser_download_url']}
    (ROOT / 'release-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PUBLIC RELEASE VERIFIED', json.dumps(result, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
