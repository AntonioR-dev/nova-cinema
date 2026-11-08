"""Prepare release-pinned NOVA Java dependencies and verified native prebuilts.
Run with Python 3.11+: python build-support/prepare.py
Only native binaries are reused from the official APK; no resources/DEX/keys.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import urllib.request
import zipfile

VIDEO = Path(__file__).resolve().parent.parent
ROOT = VIDEO.parent
PINS = {
    'MediaLib': ('aos-MediaLib', 'a07bc4f75cd9763c725c45949ebd052828e5667a'),
    'FileCoreLibrary': ('aos-FileCoreLibrary', '78ca3812e0f291e4436e4f2c92722d07b4db99f9'),
}
NAME = 'org.courville.nova-2674303-6.6.4-20261104.0822-universal-release.apk'
URL = 'https://github.com/nova-video-player/aos-AVP/releases/download/v6.6.4/' + NAME
SHA256 = '1aa2068ffec42a86efe4cee790a3f03e61194a01261405baff73ecdef1ca9ee4'


def run(*args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def prepare():
    for module, (repo, commit) in PINS.items():
        destination = ROOT / module
        if not destination.exists():
            destination.mkdir()
            run('git', 'init', destination)
            run('git', '-C', destination, 'remote', 'add', 'origin', 'https://github.com/nova-video-player/' + repo + '.git')
            run('git', '-C', destination, 'fetch', '--depth', '1', 'origin', commit)
            run('git', '-C', destination, 'checkout', '--detach', 'FETCH_HEAD')
        actual = subprocess.check_output(['git', '-C', str(destination), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != commit:
            raise RuntimeError('Refusing mismatched dependency: ' + module + ' at ' + actual)
    patch = VIDEO / 'build-support/medialib-tmdb.patch'
    if patch.exists():
        target = ROOT / 'MediaLib'
        already = subprocess.run(['git', '-C', str(target), 'apply', '--reverse', '--check', str(patch)], capture_output=True)
        if already.returncode != 0:
            run('git', '-C', target, 'apply', '--check', patch)
            run('git', '-C', target, 'apply', patch)
    downloads = ROOT / '.nova-build-cache'
    downloads.mkdir(exist_ok=True)
    apk = downloads / NAME
    if not apk.exists():
        partial = apk.with_suffix('.part')
        with urllib.request.urlopen(URL, timeout=180) as source, partial.open('wb') as output:
            shutil.copyfileobj(source, output)
        partial.replace(apk)
    with apk.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != SHA256:
        raise RuntimeError('Official APK checksum mismatch: ' + actual)
    count = 0
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            pieces = name.split('/')
            if len(pieces) != 3 or pieces[0] != 'lib' or not name.endswith('.so'):
                continue
            _, abi, filename = pieces
            if filename in ('libsentry.so', 'libsentry-android.so'):
                continue
            if abi not in ('armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'):
                raise RuntimeError('Unexpected ABI: ' + abi)
            module = 'FileCoreLibrary' if filename in ('libfilecoreutils.so', 'libnvpnativehelper.so') else 'MediaLib'
            destination = ROOT / module / 'libs' / abi / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(name))
            count += 1
    if count != 80:
        raise RuntimeError('Expected 80 native binaries, got ' + str(count))
    print('Prepared pinned dependencies and', count, 'SHA256-verified official native binaries.')


if __name__ == '__main__':
    prepare()
