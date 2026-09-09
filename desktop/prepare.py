"""Ensambla solo archivos públicos de runtime, nunca datos/configuración del usuario."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
PYTHON_VERSION = '3.14.7'
PYTHON_SHA256 = 'd297e5ff019966817ad8502465176139f2d3d840fa4ed84b13bed399a6ab1f15'
CODEX_VERSION = '0.153.4'


def get(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('linux','win'), default='linux')
    target = parser.parse_args().target
    runtime = DIST / 'runtime'
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.mkdir(parents=True)
    if target == 'linux':
        if not sys.platform.startswith('linux'):
            raise SystemExit('Construir el runtime Linux en Linux.')
        python = ROOT / '.venv' / 'bin' / 'python'
        subprocess.run([str(python), '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
            '--name', 'story-server', '--distpath', str(DIST / 'python'), '--workpath', str(DIST / 'pybuild'),
            '--specpath', str(DIST), '--add-data', f'{ROOT / "web"}:web', str(ROOT / 'app.py')], check=True, cwd=ROOT)
        shutil.copytree(DIST / 'python' / 'story-server', runtime / 'server')
        vendor = ROOT / 'node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl'
        shutil.copytree(vendor, runtime / 'codex')
        shutil.copy(Path(sysconfig.get_path('stdlib')) / 'LICENSE.txt', runtime / 'PYTHON-LICENSE.txt')
    else:
        downloads = DIST / 'downloads'
        downloads.mkdir(exist_ok=True)
        archive = downloads / f'python-{PYTHON_VERSION}-embed-amd64.zip'
        if not archive.exists():
            archive.write_bytes(get(f'https://www.python.org/ftp/python/{PYTHON_VERSION}/{archive.name}'))
        if hashlib.sha256(archive.read_bytes()).hexdigest() != PYTHON_SHA256:
            raise SystemExit('El runtime Python no coincide con el SHA256 fijado.')
        with zipfile.ZipFile(archive) as z:
            z.extractall(runtime / 'python')
        # Embeddable Python only imports from these explicit directories.
        (runtime / 'python' / 'python314._pth').write_text('python314.zip\n.\n../server\n', encoding='utf-8')
        server = runtime / 'server'
        server.mkdir()
        for name in ('app.py','workbench_ai.py','workbench_providers.py','workbench_account.py','workbench_store.py','workbench_production.py','workbench_export.py','workbench_voice.py','workbench_modes.py','workbench_realtime.py'):
            shutil.copy(ROOT / name, server / name)
        (server / 'scripts').mkdir()
        shutil.copy(ROOT / 'scripts/codex_smoke.py', server / 'scripts/codex_smoke.py')
        shutil.copytree(ROOT / 'web', server / 'web')
        # npm integrity pins the official, platform-specific Codex archive.
        meta = json.loads(get(f'https://registry.npmjs.org/@openai%2fcodex/{CODEX_VERSION}-win32-x64'))
        data = get(meta['dist']['tarball'])
        integrity = 'sha512-' + base64.b64encode(hashlib.sha512(data).digest()).decode()
        if integrity != meta['dist']['integrity']:
            raise SystemExit('Integridad del paquete Codex inválida.')
        prefix = 'package/vendor/x86_64-pc-windows-msvc/'
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
            for member in tar.getmembers():
                if not member.name.startswith(prefix) or not member.isfile():
                    continue
                relative = Path(member.name[len(prefix):])
                if relative.is_absolute() or '..' in relative.parts:
                    raise SystemExit('Ruta inválida en paquete Codex.')
                destination = runtime / 'codex' / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(tar.extractfile(member).read())
        if not (runtime / 'codex/bin/codex.exe').is_file():
            raise SystemExit('No se encontró el ejecutable Windows de Codex.')
    for name in ('CODEX-LICENSE.txt','CODEX-NOTICE.txt'):
        shutil.copy(ROOT / 'desktop' / name, runtime / name)
    from prepare_voice import prepare as prepare_voice
    prepare_voice(target, runtime / 'voice')
    files = {str(p.relative_to(runtime)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(runtime.rglob('*')) if p.is_file()}
    (runtime / 'MANIFEST.json').write_text(json.dumps({'target':target, 'codex':CODEX_VERSION, 'files':files}, indent=2))
    print(f'Runtime {target} listo: {len(files)} archivos. Sin cuentas, proyectos ni skills globales.')


if __name__ == '__main__':
    main()
