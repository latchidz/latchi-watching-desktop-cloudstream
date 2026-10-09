#!/usr/bin/env python3
"""Check eight public .cs3 packages; optionally exercise the shipping JVM host.
Network catalog failures remain recorded separately from conversion/registration.
No video from a provider is downloaded or played by this probe.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

IDS = ['3isk', 'eseek', 'Krmzy', 'MyCimaProvider', 'Topcinema', 'TukTukcima', 'Tuniflix', 'Wecima']
MANIFEST = 'https://raw.githubusercontent.com/Abodabodd/re-3arabi/refs/heads/builds/plugins.json'
MAIN_CLASS = 'com.lagradost.cloudstream3.linux.host.MainKt'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--workdir', type=Path, default=Path('verification/cs3'))
    parser.add_argument('--output', type=Path, default=Path('verification/plugins-report.json'))
    parser.add_argument('--probe-catalog', action='store_true')
    parser.add_argument('--require-catalog', action='store_true')
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(MANIFEST, timeout=30) as response:
        data = json.load(response)
    plugins = {p['internalName']: p for p in data if p.get('internalName') in IDS}
    if set(plugins) != set(IDS):
        raise RuntimeError('The public manifest no longer contains all eight requested provider IDs.')
    java = args.runtime / 'runtime/bin/java.exe' if args.runtime else None
    if java and not java.is_file():
        raise RuntimeError('Packaged Windows Java runtime is missing.')

    def host(arguments, timeout=40):
        cmd = [str(java), '-Xmx384m', '-Dfile.encoding=UTF-8', '-cp', str(args.runtime / 'provider-host/lib/*'), MAIN_CLASS, *map(str, arguments)]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', errors='replace', timeout=timeout)
        if result.returncode:
            raise RuntimeError(result.stderr[-2200:] or f'Host exited {result.returncode}')
        return json.loads(result.stdout)

    def check(ident):
        plugin = plugins[ident]
        record = {'id': ident, 'integrity': False, 'converted': False, 'registered': False, 'providers': [], 'catalog_items': 0, 'details': False, 'live_video_playback_tested': False}
        try:
            url = plugin['url']
            if not url.startswith('https://raw.githubusercontent.com/Abodabodd/re-3arabi/'):
                raise ValueError('Unexpected package origin')
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read(10 * 1024 * 1024 + 1)
            digest = hashlib.sha256(content).hexdigest()
            if len(content) != plugin['fileSize'] or 'sha256-' + digest != plugin['fileHash']:
                raise ValueError('Manifest size or SHA-256 mismatch')
            package = args.workdir / (ident + '.cs3')
            package.write_bytes(content)
            with zipfile.ZipFile(package) as archive:
                if archive.testzip() is not None:
                    raise ValueError('Package ZIP CRC mismatch')
            record.update(integrity=True, sha256=digest, size=len(content))
            if not java:
                return record
            artifact = args.workdir / (ident + '.jar')
            host(['convert', package, artifact], timeout=55)
            record['converted'] = artifact.is_file()
            providers = host(['list', artifact, 'auto'], timeout=30)
            if not isinstance(providers, list) or not providers:
                raise ValueError('No compatible provider registered')
            record['providers'] = [p['name'] for p in providers]
            record['registered'] = True
            if args.probe_catalog:
                try:
                    provider = providers[0]['name']
                    sections = host(['home', artifact, 'auto', provider], timeout=45)
                    titles = []
                    if isinstance(sections, list):
                        for section in sections:
                            titles.extend(section.get('list', section.get('items', [])))
                    record['catalog_items'] = len(titles)
                    if titles:
                        title = next((x for x in titles if x.get('url')), None)
                        if title:
                            try:
                                details = host(['load', artifact, 'auto', provider, title['url']], timeout=40)
                                record['details'] = isinstance(details, dict) and bool(details.get('name'))
                            except Exception as error:
                                record['details_error'] = str(error)[-2200:]
                except Exception as error:
                    record['catalog_error'] = str(error)[-2200:]
        except Exception as error:
            record['runtime_error'] = str(error)[-2200:]
        return record

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(check, IDS))
    report = {'platform': sys.platform, 'source_commit': os.environ.get('GITHUB_SHA'), 'manifest': MANIFEST,
              'runtime_tested': bool(java), 'packages': results,
              'integrity_passed': sum(x['integrity'] for x in results),
              'registration_passed': sum(x['registered'] for x in results),
              'catalogs_with_items': sum(x['catalog_items'] > 0 for x in results),
              'details_passed': sum(x['details'] for x in results),
              'live_provider_playback_tested': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for result in results:
        print(result['id'], 'integrity=' + str(result['integrity']), 'registered=' + str(result['registered']),
              'catalog_items=' + str(result['catalog_items']), 'details=' + str(result['details']), flush=True)
    if report['integrity_passed'] != 8 or (java and report['registration_passed'] != 8):
        raise SystemExit('Required package conversion/registration checks did not all pass. See the report.')
    if args.require_catalog and (not report['catalogs_with_items'] or not report['details_passed']):
        raise SystemExit('No provider completed a real catalog/details round trip. Release is blocked.')

if __name__ == '__main__':
    main()
