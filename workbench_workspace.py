"""Carpetas locales elegidas por el autor; originales siempre de solo lectura."""
import json
import os
from pathlib import Path
import re
from workbench_store import MAX_TEXT, Problem, atomic, check, is_link, text_value

EXTENSIONS = ('.md', '.markdown', '.txt')
SKIP = {'node_modules', 'target', 'dist', '__pycache__', 'venv'}


def directory(value):
    text_value(value, 4000, False)
    path = Path(value)
    check(path.is_absolute() and '..' not in path.parts, 'Elegí una ruta absoluta.')
    check(not any(is_link(p) for p in (path, *path.parents)), 'No se permiten carpetas enlazadas.')
    check(path.is_dir(), 'La carpeta no está disponible.')
    return path


def import_preview(value):
    root = directory(value)
    files, skipped, visited = [], 0, 0
    def fail(error):
        raise error
    for base, dirs, names in os.walk(root, followlinks=False, onerror=fail):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in SKIP and not is_link(Path(base)/d))
        visited += len(dirs) + len(names)
        check(visited <= 10000, 'La carpeta es demasiado grande. Elegí una subcarpeta.')
        for name in sorted(names):
            path = Path(base)/name
            if name.startswith('.') or path.suffix.lower() not in EXTENSIONS or is_link(path) or not path.is_file():
                skipped += 1
                continue
            relative = path.relative_to(root).as_posix()
            files.append(dict(name=relative, size=path.stat().st_size,
                              role='manuscrito' if any(p in ('manuscript','manuscrito') for p in path.relative_to(root).parts[:-1]) else 'referencia'))
            check(len(files) <= 1000, 'Hay demasiados textos. Elegí una subcarpeta.')
    return dict(path=str(root), files=files, skipped=skipped)


def import_documents(value, names):
    root = directory(value)
    check(isinstance(names, list) and 0 < len(names) <= 100 and all(isinstance(n,str) for n in names),
          'Elegí entre 1 y 100 archivos.')
    check(len(set(names)) == len(names), 'Hay archivos repetidos.')
    allowed = {f['name']: f for f in import_preview(value)['files']}
    docs = []
    for name in names:
        check(name in allowed, 'La selección cambió o contiene una ruta no permitida.')
        path = root / name
        check(not any(is_link(p) for p in (path, *path.parents)), 'No se importan enlaces.')
        with path.open('rb') as source:
            content = source.read(MAX_TEXT + 1).decode('utf-8-sig')
        text_value(content)
        docs.append(dict(name=name, role=allowed[name]['role'], content=content))
    return docs


class Workspace:
    def __init__(self, default):
        self.default = Path(default).absolute()
        check(not any(is_link(p) for p in (self.default, *self.default.parents)), 'El espacio no puede ser un enlace.')
        self.default.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory(str(self.default))
        self.preference = self.default / '.workspace.json'
        self.active = self.default
        self.warning = ''
        self.pending = self.default
        try:
            if self.preference.exists():
                check(not is_link(self.preference), 'Preferencia enlazada.')
                value = text_value(json.loads(self.preference.read_text())['path'],4000,False)
                self.pending = Path(value)
                directory(value)
                self.validate(self.pending)
                self.active = self.pending
        except (OSError, ValueError, KeyError, TypeError, Problem):
            # La ubicación desconectada nunca se recrea ni pierde su preferencia.
            self.warning = 'No se pudo abrir el espacio elegido. Se muestra la biblioteca predeterminada; revisá la ubicación en Configuración.'

    def validate(self, path):
        if path == self.default:
            return
        marker = path / '.story-workbench'
        check(not is_link(marker) and marker.is_file() and marker.read_text() == '1',
              'Elegí una carpeta vacía o un espacio de Story Workbench. Para una obra existente, usá Importar carpeta.')

    def status(self):
        return dict(active=str(self.active), pending=str(self.pending), default=str(self.default),
                    restart=self.active != self.pending, warning=self.warning)

    def choose(self, value, name=''):
        parent = directory(value)
        text_value(name,160)
        if name:
            text_value(name, 160, False)
            check(name.strip() == name and name not in ('.','..') and not re.search(r'[\\/:<>"|?*\x00-\x1f]', name)
                  and not name.endswith('.') and not re.fullmatch(r'(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',name), 'Nombre de carpeta inválido.')
            path = parent / name
            check(not path.exists() and not is_link(path), 'Esa carpeta ya existe. Elegila sin crear otra.')
            path.mkdir(mode=0o700)
        else:
            path = parent
        if path != self.default and not any(path.iterdir()):
            atomic(path / '.story-workbench', '1')
        self.validate(path)
        atomic(self.preference, json.dumps(dict(path=str(path))))
        self.pending = path
        self.warning = ''
        return self.status()
