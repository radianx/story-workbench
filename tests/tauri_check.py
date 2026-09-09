"""Prueba de la ventana Tauri real con corpus temporal; sin cuenta ni API; micrófono virtual de WebKit."""
import os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
command=ROOT/'src-tauri/target/debug/story-workbench-tauri'
with tempfile.TemporaryDirectory(prefix='sw-tauri-test-') as directory:
    env={**os.environ,'STORY_TEST_DATA':directory,'STORY_TAURI_SMOKE':'1'}
    try:
        for launch in range(2):
            result=subprocess.run([str(command)],env=env,capture_output=True,text=True,timeout=90)
            print(result.stdout)
            if result.returncode:print(result.stderr[-3000:])
            assert result.returncode==0,result.returncode
            assert 'Tauri smoke: OK' in result.stdout
        for file in Path(directory).rglob('*'):
            if file.is_file():assert b'AQ.fixture-not-a-real-key-tauri' not in file.read_bytes(),file
    finally:
        subprocess.run([str(command)],env={**env,'STORY_TAURI_CLEANUP':'1'},check=True,timeout=30)
    assert (Path(directory)/'projects').is_dir()
    assert not (Path(directory)/'codex/auth.json').exists()
print('OK Tauri: sidecar, interfaz WebKit, proyecto ficticio, editor, navegación, tema entre reinicios, libro y exportación HTTP. Claves ficticias guardadas/recuperadas/borradas en llavero nativo, audio virtual, cámara denegada, lectura local, transporte Gemini y lectura OpenAI/Gemini simulados. WebRTC se informa por separado.')
