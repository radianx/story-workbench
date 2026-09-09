"""Ejecutar el paquete Linux con datos temporales y sin Python/Codex en PATH."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='sw-desktop-') as temp:
    env={**os.environ,'STORY_TEST_DATA':temp,'STORY_DESKTOP_SMOKE':'1','PATH':'/usr/bin:/bin'}
    # Test-only: Ubuntu restricts user namespaces in an uninstalled unpacked app.
    # The shipped app never disables sandboxing; the .deb configures chrome-sandbox.
    result=subprocess.run([str(ROOT/'dist/installers/linux-unpacked/story-workbench'),'--headless','--disable-gpu','--no-sandbox'],
                          env=env,text=True,capture_output=True,timeout=55)
    print(result.stdout)
    if result.returncode:
        print(result.stderr[-4000:])
    assert result.returncode==0, result.returncode
    assert 'OK Electron' in result.stdout
    result=subprocess.run([str(ROOT/'dist/installers/linux-unpacked/story-workbench'),'--headless','--disable-gpu','--no-sandbox'],
                          env=env,text=True,capture_output=True,timeout=55)
    assert result.returncode==0, result.stderr[-1000:]
    assert '"persistent":true' in result.stdout, result.stdout
    print('OK preferencias conservadas al reiniciar con otro puerto local.')
    assert (Path(temp)/'projects').is_dir()
    assert not (Path(temp)/'codex/auth.json').exists()
