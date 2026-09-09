"""Preparar sidecar nativo Tauri desde el runtime ya verificado de Electron; sin datos del usuario."""
import hashlib,json,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    target='win' if sys.platform=='win32' else 'linux' if sys.platform.startswith('linux') else None
    if not target or platform.machine().lower() not in ('amd64','x86_64'):
        raise SystemExit('Este primer corte prepara Linux/Windows x64 desde su sistema nativo.')
    source=ROOT/'dist/installers'/f'{target}-unpacked/resources/runtime'
    manifest=json.loads((source/'MANIFEST.json').read_text())
    for name,digest in manifest['files'].items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=digest:
            raise SystemExit('El runtime de origen no coincide con su manifiesto.')
    dest=ROOT/'src-tauri/runtime'
    if dest.exists():shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in ('codex','voice'):shutil.copytree(source/name,dest/name)
    for path in source.glob('*.txt'):shutil.copy(path,dest/path.name)
    for path in source.glob('*.json'):
        if path.name!='MANIFEST.json':shutil.copy(path,dest/path.name)
    binary=ROOT/'src-tauri/binaries';binary.mkdir(exist_ok=True)
    triple='x86_64-pc-windows-msvc' if target=='win' else 'x86_64-unknown-linux-gnu'
    python=ROOT/'.venv'/('Scripts/python.exe' if target=='win' else 'bin/python')
    subprocess.run([str(python),'-m','PyInstaller','--noconfirm','--clean','--onefile',
        '--name',f'story-server-{triple}','--distpath',str(binary),
        '--workpath',str(ROOT/'dist/tauri-pybuild'),'--specpath',str(ROOT/'dist'),
        '--add-data',f'{ROOT/"web"}:web',str(ROOT/'app.py')],check=True,cwd=ROOT)
    files={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()}
    (dest/'MANIFEST.json').write_text(json.dumps({'target':target,'files':files},indent=2)+'\n')
    print(f'Sidecar {triple} y recursos públicos listos. Sin cuentas, claves ni proyectos.')

if __name__=='__main__':main()
