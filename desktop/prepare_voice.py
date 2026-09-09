"""Motor Vosk y modelo español fijados; solo artefactos públicos, sin audio del usuario."""
import hashlib
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    'linux': ('vosk-linux.whl', 'https://files.pythonhosted.org/packages/fc/ca/83398cfcd557360a3d7b2d732aee1c5f6999f68618d1645f38d53e14c9ff/vosk-0.3.45-py3-none-manylinux_2_12_x86_64.manylinux2010_x86_64.whl', '25e025093c4399d7278f543568ed8cc5460ac3a4bf48c23673ace1e25d26619f'),
    'win': ('vosk-win.whl', 'https://files.pythonhosted.org/packages/c0/4c/deb0861f7da9696f8a255f1731bb73e9412cca29c4b3888a3fcb2a930a59/vosk-0.3.45-py3-none-win_amd64.whl', '6994ddc68556c7e5730c3b6f6bad13320e3519b13ce3ed2aa25a86724e7c10ac'),
    'model': ('vosk-model-small-es-0.42.zip', 'https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip', '09b239888f633ef2f0b4e09736e3d9936acfd810bc65d53fad45261762c6511f'),
}


def archive(asset):
    name, url, expected = ASSETS[asset]
    path = ROOT / 'dist/downloads/voice' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(url, timeout=120) as response:
            path.write_bytes(response.read())
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('El recurso de voz no coincide con su SHA256: ' + name)
    return zipfile.ZipFile(path)


def prepare(target, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with archive(target) as engine:
        for name in engine.namelist():
            if name.startswith('vosk/') and name.endswith(('.so', '.dll')):
                (destination / Path(name).name).write_bytes(engine.read(name))
    with archive('model') as model:
        for name in model.namelist():
            if name.endswith('/'):
                continue
            relative = Path(name).relative_to('vosk-model-small-es-0.42')
            if '..' in relative.parts or relative.is_absolute():
                raise ValueError('Ruta de modelo inválida.')
            path = destination / 'model' / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(model.read(name))
    shutil.copytree(ROOT / 'desktop/voice-licenses', destination / 'licenses', dirs_exist_ok=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=('linux', 'win'), default='linux')
    target = parser.parse_args().target
    prepare(target, ROOT / 'dist/voice' / target)
    print('Voz local preparada:', target)
