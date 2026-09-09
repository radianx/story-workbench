"""Build local Tauri installers with an isolated Linux toolchain; no private files mounted."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('linux', 'win'), required=True)
    parser.add_argument('--skip-prepare', action='store_true', help='Reuse a verified runtime for the same target')
    args = parser.parse_args()
    if not args.skip_prepare:
        subprocess.run([sys.executable, str(ROOT/'desktop/prepare.py'), '--target', args.target], check=True)
    runtime = ROOT/'src-tauri/runtime'
    manifest = json.loads((runtime/'MANIFEST.json').read_text())
    assert manifest['target'] == args.target, 'Preparar el runtime correcto antes de compilar.'
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((runtime/name).read_bytes()).hexdigest() == digest, name
    cache = Path(os.environ.get('STORY_BUILD_CACHE', '/tmp/sw-tauri-cargo'))
    cache.mkdir(parents=True, exist_ok=True)
    base = ['docker', 'run', '--rm', '--user', f'{os.getuid()}:{os.getgid()}',
            '-e', 'CARGO_HOME=/cargo', '-e', 'CARGO_BUILD_JOBS=4', '-e', 'XWIN_CACHE_DIR=/cargo/xwin',
            '-e', 'XDG_CACHE_HOME=/cargo/cache',
            '--mount', f'type=bind,src={cache},dst=/cargo']
    for source, dest, readonly in [('src-tauri','src-tauri',False),('web','web',True),('desktop/sidecar','sidecar',True)]:
        base += ['--mount', f'type=bind,src={ROOT/source},dst=/workspace/{dest}' + (',readonly' if readonly else '')]
    base += ['story-workbench-tauri-build']
    if args.target == 'win':
        subprocess.run(base + ['sh', '-c', 'RUSTFLAGS="-C target-feature=+crt-static" cargo xwin build --locked --release --manifest-path sidecar/Cargo.toml --target-dir src-tauri/target/sidecar --target x86_64-pc-windows-msvc && cp src-tauri/target/sidecar/x86_64-pc-windows-msvc/release/story-server.exe src-tauri/binaries/story-server-x86_64-pc-windows-msvc.exe'], check=True)
        command = 'cd src-tauri && tauri build --runner cargo-xwin --target x86_64-pc-windows-msvc --bundles nsis -- --locked'
        bundles = ROOT/'src-tauri/target/x86_64-pc-windows-msvc/release/bundle/nsis'
        pattern, suffix = '*.exe', 'win-x64.exe'
    else:
        command = 'cd src-tauri && tauri build --bundles deb -- --locked'
        bundles = ROOT/'src-tauri/target/release/bundle/deb'
        pattern, suffix = '*.deb', 'linux-amd64.deb'
    subprocess.run(base + ['sh', '-c', command], check=True)
    version = json.loads((ROOT/'src-tauri/tauri.conf.json').read_text())['version']
    packages = [package for package in bundles.glob(pattern) if f'_{version}_' in package.name]
    assert len(packages) == 1, 'Revisar paquetes de builds anteriores.'
    output = ROOT/'dist/installers'; output.mkdir(parents=True, exist_ok=True)
    destination = output/f'Story-Workbench-{version}-{suffix}'
    shutil.copy2(packages[0], destination)
    # Preserve hashes of historical packages while updating this release.
    hashes = output/'SHA256SUMS'
    lines = hashes.read_text().splitlines() if hashes.exists() else []
    lines = [line for line in lines if line.split()[-1] != destination.name]
    lines.append(f'{hashlib.sha256(destination.read_bytes()).hexdigest()}  {destination.name}')
    hashes.write_text('\n'.join(lines)+'\n')
    print(destination)


if __name__ == '__main__':
    main()
