"""Verify extracted installers against public runtime manifests and final package hashes."""
import argparse,hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--linux-root',type=Path,required=True,help='dpkg-deb -x output')
parser.add_argument('--windows-root',type=Path,required=True,help='7z x output for NSIS')
args=parser.parse_args()
version=json.loads((ROOT/'src-tauri/tauri.conf.json').read_text())['version']
for target,base in [('linux',args.linux_root/'usr/lib/Story Workbench'),('win',args.windows_root)]:
    runtime=base/'runtime';manifest=json.loads((runtime/'MANIFEST.json').read_text())
    assert manifest['target']==target
    assert (runtime/'LICENSE').read_bytes()==(ROOT/'LICENSE').read_bytes()
    actual={p.relative_to(runtime).as_posix() for p in runtime.rglob('*') if p.is_file()}
    assert actual==set(manifest['files'])|{'MANIFEST.json'}, actual-set(manifest['files'])-{'MANIFEST.json'}
    for name,digest in manifest['files'].items():
        assert hashlib.sha256((runtime/name).read_bytes()).hexdigest()==digest,name
        assert not set(Path(name).parts)&{'projects','auth.json','voice-keys','editor-keys','.codex'},name
    assert (runtime/('codex/bin/codex.exe' if target=='win' else 'codex/bin/codex')).is_file()
    assert (runtime/'voice/model/am/final.mdl').is_file()
    if target=='win':
        assert (runtime/'server/workbench_team.py').is_file()
        assert (runtime/'server/web/team.js').is_file()
        for name in ('story-server.exe','story-workbench.exe'):
            imports=subprocess.check_output(['objdump','-p',str(base/name)],text=True)
            assert 'DLL Name: VCRUNTIME' not in imports and 'DLL Name: MSVCP' not in imports,name
        assert (base/'story-server.exe').read_bytes()==(ROOT/'src-tauri/binaries/story-server-x86_64-pc-windows-msvc.exe').read_bytes()
        assert (base/'story-server.exe').read_bytes()[:2]==b'MZ'
        assert (base/'story-workbench.exe').read_bytes()[:2]==b'MZ'
        assert (base/'$TEMP/MicrosoftEdgeWebview2Setup.exe').is_file()
        for file in (runtime/'server').glob('*.py'):assert file.read_bytes()==(ROOT/file.name).read_bytes(),file.name
        for file in (runtime/'server/web').rglob('*'):
            if file.is_file():assert file.read_bytes()==(ROOT/'web'/file.relative_to(runtime/'server/web')).read_bytes(),file.name
    else:
        for name in ('story-workbench','story-server'):
            assert (args.linux_root/'usr/bin'/name).read_bytes()[:4]==b'\x7fELF'
        assert (args.linux_root/'usr/bin/story-server').read_bytes()==(ROOT/'src-tauri/binaries/story-server-x86_64-unknown-linux-gnu').read_bytes()
    suffix='linux-amd64.deb' if target=='linux' else 'win-x64.exe'
    file=ROOT/'dist/installers'/f'Story-Workbench-{version}-{suffix}'
    record=f'{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.name}'
    assert record in (file.parent/'SHA256SUMS').read_text().splitlines()
    print(f'OK {target}: {len(actual)} archivos de runtime verificados y SHA256 del instalador.')
