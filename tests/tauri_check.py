"""Prueba de la ventana Tauri real con corpus temporal; sin cuenta, API ni micrófono."""
import os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
command=ROOT/'src-tauri/target/debug/story-workbench-tauri'
with tempfile.TemporaryDirectory(prefix='sw-tauri-test-') as directory:
    for launch in range(2):
        result=subprocess.run([str(command)],env={**os.environ,'STORY_TEST_DATA':directory,'STORY_TAURI_SMOKE':'1'},capture_output=True,text=True,timeout=90)
        print(result.stdout)
        if result.returncode:print(result.stderr[-3000:])
        assert result.returncode==0,result.returncode
        assert 'Tauri smoke: OK' in result.stdout
    assert (Path(directory)/'projects').is_dir()
    assert not (Path(directory)/'codex/auth.json').exists()
print('OK Tauri: sidecar, interfaz WebKit, proyecto ficticio, editor, navegación, tema entre reinicios, libro y exportación HTTP. Almacén persistente y voz no validados.')
