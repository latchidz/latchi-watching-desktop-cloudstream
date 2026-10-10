#!/usr/bin/env python3
"""Publish only tested Windows outputs; never move old tags or replace old assets."""
import hashlib,json,os,re,subprocess,urllib.request,urllib.error
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'output'
SRC='latchidz/latchi-watching-desktop-cloudstream';DIST='latchidz/LATCHI-RELEASES'
TOKEN=os.environ.get('LATCHI_RELEASE_TOKEN','');SHA=os.environ['GITHUB_SHA']
import xml.etree.ElementTree as ET
VERSION=ET.parse('src/LatchiWatching.App/LatchiWatching.App.csproj').findtext('.//Version')
TAG='watching-windows-v'+VERSION

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def api(method,path,data=None,missing=False):
    h={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'LATCHI-WATCHING-release','Content-Type':'application/json'}
    req=urllib.request.Request('https://api.github.com'+path,headers=h,method=method,data=None if data is None else json.dumps(data).encode())
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            b=r.read();return json.loads(b) if b else None
    except urllib.error.HTTPError as e:
        if missing and e.code==404:return None
        raise RuntimeError(f'GitHub {method} HTTP {e.code}: {path}') from None

def main():
    if not TOKEN:raise RuntimeError('Temporary publishing secret missing; no release created.')
    assert re.fullmatch('[0-9a-f]{40}',SHA) and re.fullmatch(r'\d+\.\d+\.\d+',VERSION)
    report=json.loads((OUT/'WINDOWS-VERIFICATION.json').read_text(encoding='utf-8-sig'))
    assert report['source_commit']==SHA and report['version']==VERSION
    assert report['ui']['passed'] and report['unit_tests_passed']>=20
    assert report['installer_install_and_launch_passed'] and report['fresh_portable_passed'] and report['uninstall_preserved_user_file']
    required=[f'LATCHI-WATCHING-{VERSION}-Windows-x64-Setup.exe',f'LATCHI-WATCHING-{VERSION}-Windows-x64.zip',f'LATCHI-WATCHING-{VERSION}-source.zip',f'LATCHI-WATCHING-{VERSION}-Artwork-3x1.zip']
    assert all((OUT/x).is_file() for x in required)
    marker='<!-- LATCHI_SOURCE_COMMIT='+SHA+' -->'
    notes=f'''# LATCHI WATCHING {VERSION} — Windows websites edition

بناء مستقل على هيكل WPF/WebView2 ومشغّل LATCHI PLAY، حسب اختيار المالك.

- ثمانية مصادر فقط، بطاقات في وسط الشاشة وتخطيط عربي RTL.
- تسع صور سينمائية جديدة، كلها **1800×600 / 3:1 فعلية**؛ الأسماء والشعارات مضبوطة خارج مولّد الصور.
- كل بطاقة تفتح موقع المصدر ومشغّله الأصلي في شاشة كاملة، مع حظر النوافذ المنبثقة والخروج بـEsc.
- إعدادات لتحديث نطاق المصدر، وملف بيانات مستقل عن Play وElectron.
- لا TMDB، لا vidfast بديل للمصادر، **ولا Runtime لإضافات `.cs3`** في هذه النسخة؛ هذا هو المسار الذي اختاره المالك.

## التحقق الفعلي
- {report['unit_tests_passed']} اختبار وحدات/أمان عناوين نجح على Windows.
- WebView2 عرض البطاقات الثماني فعليًا؛ لقطة Windows مرفقة.
- فيديو VP8 محلي مولّد قانونيًا: فك/تصيير/إيقاف/بحث، شاشة كاملة، وحظر window.open.
- تشغيل المثبّت والنسخة المحمولة بعد فك جديد نجح؛ إلغاء التثبيت أبقى ملف المستخدم المضاف.
- المصدر المطابق: https://github.com/{SRC}/tree/{TAG}

## حدود واضحة
المثبّت **غير موقّع**. لا تعطّل حماية Windows. المواقع خدمات أطراف ثالثة وقد تتوقف أو تمنع الشبكة؛
لم نثبت التشغيل الحي لكل مقاطع المواقع الثمانية أو جهاز GPU/صوت حقيقي.
يتطلب Microsoft Edge WebView2 Evergreen. .NET مضمّن. لا توجد ترقية تلقائية أو نقل بيانات من Electron.
شاهد فقط المحتوى الذي تملك حق الوصول إليه.

Setup للتثبيت، ZIP محمول، Artwork-3x1 للصور التسع، source للمصدر المطابق،
SHA256SUMS للبصمات، INSTALL-AR للتعليمات، WINDOWS-VERIFICATION للنتائج.

{marker}
'''
    (ROOT/'release-notes.md').write_text(notes,encoding='utf-8')
    ref=api('GET',f'/repos/{SRC}/git/ref/tags/{TAG}',missing=True)
    if ref:
        if ref['object']['sha']!=SHA:raise RuntimeError('Source tag is immutable; increase version, do not replace it.')
    else:api('POST',f'/repos/{SRC}/git/refs',{'ref':'refs/tags/'+TAG,'sha':SHA})
    release=api('GET',f'/repos/{DIST}/releases/tags/{TAG}',missing=True)
    env=os.environ.copy();env['GH_TOKEN']=TOKEN
    if release:
        if marker not in release.get('body',''):raise RuntimeError('Existing release belongs to another revision; not overwritten.')
    else:
        subprocess.run(['gh','release','create',TAG,'--repo',DIST,'--draft','--latest=false','--title','LATCHI WATCHING '+VERSION+' — Windows','--notes-file','release-notes.md'],env=env,check=True)
        release=api('GET',f'/repos/{DIST}/releases/tags/{TAG}')
    files=sorted(x for x in OUT.iterdir() if x.is_file())
    existing={a['name']:a for a in release['assets']}
    for path in files:
        if path.name in existing:
            if existing[path.name].get('digest')!='sha256:'+sha(path):raise RuntimeError('Existing asset differs; never overwrite: '+path.name)
        else:
            if not release['draft']:raise RuntimeError('Public release is immutable; missing asset: '+path.name)
            subprocess.run(['gh','release','upload',TAG,str(path),'--repo',DIST],env=env,check=True)
    release=api('GET',f'/repos/{DIST}/releases/{release["id"]}')
    assets={a['name']:a for a in release['assets']}
    for path in files:
        assert assets[path.name]['size']==path.stat().st_size and assets[path.name].get('digest')=='sha256:'+sha(path),path.name
    if release['draft']:release=api('PATCH',f'/repos/{DIST}/releases/{release["id"]}',{'draft':False,'make_latest':'false','prerelease':False})
    result={'version':VERSION,'source_commit':SHA,'release':release['html_url'],'installer':assets[required[0]]['browser_download_url'],'portable':assets[required[1]]['browser_download_url'],'source':assets[required[2]]['browser_download_url'],'artwork':assets[required[3]]['browser_download_url'],'installer_sha256':assets[required[0]]['digest'],'checksums':assets['SHA256SUMS.txt']['browser_download_url']}
    (ROOT/'release-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('PUBLIC_RELEASE_VERIFIED',json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
