"""Ejecutar el paquete Linux con datos temporales y sin Python/Codex en PATH."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--installed', action='store_true')
parser.add_argument('--voice', action='store_true')
options=parser.parse_args()
installed=options.installed
command=['/usr/bin/story-workbench' if installed else str(ROOT/'dist/installers/linux-unpacked/story-workbench'),'--headless','--disable-gpu']
if not installed: command.append('--no-sandbox')
if options.voice: command.append('--use-fake-device-for-media-stream')
with tempfile.TemporaryDirectory(prefix='sw-desktop-') as temp:
    env={**os.environ,'STORY_TEST_DATA':temp,'STORY_DESKTOP_SMOKE':'1','PATH':'/usr/bin:/bin'}
    if options.voice: env['STORY_VOICE_SMOKE']='1'
    # Test-only: Ubuntu restricts user namespaces in an uninstalled unpacked app.
    # The shipped app never disables sandboxing; the .deb configures chrome-sandbox.
    result=subprocess.run(command,
                          env=env,text=True,capture_output=True,timeout=120)
    print(result.stdout)
    if result.returncode:
        print(result.stderr[-4000:])
    assert result.returncode==0, result.returncode
    assert 'OK Electron' in result.stdout
    native='OK almacén nativo: clave ficticia cifrada' in result.stdout
    result=subprocess.run(command,
                          env=env,text=True,capture_output=True,timeout=120)
    if native:
        assert 'OK almacén nativo: recuperado al reiniciar y eliminado' in result.stdout,result.stdout
        assert not (Path(temp)/'voice-keys/gemini.bin').exists()
        print('OK clave ficticia recuperada del almacén nativo tras reinicio y eliminada.')
    assert result.returncode==0, result.stderr[-1000:]
    assert '"persistent":true' in result.stdout, result.stdout
    print('OK preferencias conservadas al reiniciar con otro puerto local.')
    assert (Path(temp)/'projects').is_dir()
    assert not (Path(temp)/'codex/auth.json').exists()
