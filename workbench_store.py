"""Archivos Markdown privados y metadatos locales; sin dependencias."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
import uuid

MAX_TEXT = 250_000
ROLES = ('manuscrito', 'canon', 'estilo', 'referencia', 'plan', 'traducción')


class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def check(condition, message, status=400):
    if not condition:
        raise Problem(message, status)


def uid():
    return uuid.uuid4().hex


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def text_value(value, limit=MAX_TEXT, empty=True):
    check(isinstance(value, str) and len(value.encode('utf-8')) <= limit and '\0' not in value,
          'Texto inválido o demasiado grande.')
    check(empty or bool(value.strip()), 'Completá el texto.')
    return value


def atomic(path, text):
    check(not path.is_symlink(), 'No se permiten enlaces simbólicos.')
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.save-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class Store:
    # ponytail: un proceso y un lock local; usar transacciones si hay varios servidores.
    def __init__(self, root):
        self.root = Path(root).absolute()
        check(not any(p.is_symlink() for p in (self.root, *self.root.parents)),
              'El directorio de datos no puede ser un enlace.')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        for project in self.list_projects():
            data = self.load(project['id'])
            changed = False
            for run in data['runs']:
                if run['status'] in ('running', 'connecting', 'cancelling'):
                    run.update(status='interrupted', error='El servicio se reinició. Podés volver a pedir la tarea.')
                    changed = True
            if changed:
                self.persist(data)

    def path(self, project, *parts):
        check(isinstance(project, str) and re.fullmatch('[a-f0-9]{32}', project), 'Proyecto inválido.')
        path = self.root / project
        for part in parts:
            check(isinstance(part, str) and part not in ('.', '..') and '/' not in part and '\\' not in part,
                  'Ruta inválida.')
            path /= part
        check(not any(p.is_symlink() for p in (path, *path.parents)), 'No se permiten enlaces simbólicos.')
        check(path.is_relative_to(self.root), 'Ruta fuera del proyecto.')
        return path

    def list_projects(self):
        projects = []
        for path in self.root.iterdir():
            if re.fullmatch('[a-f0-9]{32}', path.name):
                data = self.load(path.name)
                projects.append({k: data[k] for k in ('id', 'title', 'updated')})
        return sorted(projects, key=lambda p: p['updated'], reverse=True)

    def load(self, project):
        path = self.path(project, 'project.json')
        check(path.is_file(), 'Proyecto no encontrado.', 404)
        return json.loads(path.read_text(encoding='utf-8'))

    def persist(self, data):
        data['updated'] = time.time()
        atomic(self.path(data['id'], 'project.json'), json.dumps(data, ensure_ascii=False))

    def create(self, title, demo=False):
        text_value(title, 160, False)
        project = uid()
        path = self.path(project)
        path.mkdir(mode=0o700)
        for name in ('documents', 'history', 'agent'):
            (path / name).mkdir(mode=0o700)
        data = dict(id=project, title=title, updated=time.time(), documents=[], proposals=[],
                    decisions=[], runs=[], thread=None, context_key=None)
        self.persist(data)
        if demo:
            examples = [
                ('01 · La última luz.md', 'manuscrito', '# La última luz\n\nInés dejó la llave azul sobre la mesa del faro. Afuera, el agua borraba el camino.\n\n—Mi padre vuelve el viernes —dijo.\n\nTomás miró el calendario. Era jueves. Hacía tres años que habían enterrado a Julián.\n\nLa radio crujió. Inés reconoció la voz antes de escuchar su nombre.\n'),
                ('Canon del faro.md', 'canon', '# Canon aprobado\n\n- Inés tiene veintinueve años.\n- Su padre, Julián, murió hace tres años.\n- La llave del cuarto de radio es roja.\n- Tomás no conoce la voz de Julián.\n\n# Idea provisional\n\nLa transmisión podría ser una grabación. No está decidido.\n'),
                ('Voz y tono.md', 'estilo', '# Voz y tono\n\nTercera persona cercana a Inés. Pasado. Diálogos breves con voseo.\nConservar la incertidumbre sobre la radio. No explicar aún su origen.\nEvitar convertir las imágenes en explicaciones.\n'),
                ('02 · El cuarto de radio.md', 'manuscrito', '# El cuarto de radio\n\nInés giró la llave roja. Tomás esperó al otro lado de la puerta.\n\nLa voz volvió a llamarla. Ella no contestó.\n')]
            for name, role, content in examples:
                self.add_document(project, name, role, content)
        return self.load(project)

    def document(self, data, document):
        found = next((d for d in data['documents'] if d['id'] == document), None)
        check(found is not None, 'Documento no encontrado.', 404)
        path = self.path(data['id'], 'documents', found['id'] + '.md')
        check(path.stat().st_size <= MAX_TEXT, 'Documento demasiado grande.')
        content = path.read_bytes().decode('utf-8')
        return {**found, 'content': content, 'hash': digest(content)}

    def snapshot(self, project):
        data = self.load(project)
        data['documents'] = [self.document(data, d['id']) for d in data['documents']]
        # Los snapshots de contexto quedan privados; la UI recibe referencias, no duplicados completos.
        for run in data['runs']:
            run.pop('source_texts', None)
        return data

    def add_document(self, project, name, role, content):
        text_value(name, 200, False)
        text_value(content)
        check(role in ROLES, 'Rol inválido.')
        data = self.load(project)
        check(len(data['documents']) < 100, 'Límite del prototipo: 100 documentos por proyecto.')
        document = dict(id=uid(), name=name, role=role, selected=True, history=[])
        atomic(self.path(project, 'documents', document['id'] + '.md'), content)
        data['documents'].append(document)
        self.persist(data)
        return self.document(data, document['id'])

    def save_document(self, data, document, content, expected, reason='Guardado manual'):
        text_value(content)
        current = self.document(data, document)
        check(current['hash'] == expected, 'El documento cambió. Recargá o copiá tu borrador antes de continuar.', 409)
        if current['content'] == content:
            return current
        version = dict(id=uid(), date=time.time(), reason=reason)
        atomic(self.path(data['id'], 'history', version['id'] + '.md'), current['content'])
        meta = next(d for d in data['documents'] if d['id'] == document)
        meta['history'].append(version)
        # La versión recuperable se registra antes de reemplazar el documento.
        self.persist(data)
        check(self.document(data, document)['hash'] == expected, 'Cambio externo durante el guardado.', 409)
        atomic(self.path(data['id'], 'documents', document + '.md'), content)
        self.persist(data)
        return self.document(data, document)

    def proposals_from_result(self, data, run, proposals):
        check(isinstance(proposals, list) and len(proposals) <= 20, 'Respuesta de propuestas inválida.')
        prepared = []
        for item in proposals:
            check(isinstance(item, dict), 'Bloque inválido.')
            document = item.get('document_id')
            check(document in run['source_texts'], 'Propuesta fuera del contexto seleccionado.')
            before = text_value(item.get('before'), empty=False)
            after = text_value(item.get('after'))
            reason = text_value(item.get('reason'), 4000, False)
            source = run['source_texts'][document]
            check(source.count(before) == 1 and before != after, 'El pasaje propuesto no es único o no cambia.')
            prepared.append(dict(id=uid(), document=document, before=before, after=after,
                                 reason=reason, status='pending', run=run['id'], base=digest(source)))
        data['proposals'].extend(prepared)

    def decide(self, project, proposal_id, accept):
        data = self.load(project)
        proposal = next((p for p in data['proposals'] if p['id'] == proposal_id), None)
        check(proposal is not None and proposal['status'] == 'pending', 'Propuesta no disponible.', 409)
        if accept:
            current = self.document(data, proposal['document'])
            check(current['hash'] == proposal['base'], 'La propuesta quedó desactualizada. Pedí una nueva revisión.', 409)
            check(current['content'].count(proposal['before']) == 1, 'El pasaje ya no coincide.', 409)
            updated = current['content'].replace(proposal['before'], proposal['after'], 1)
            self.save_document(data, proposal['document'], updated, current['hash'], 'Propuesta aceptada')
            # Solo avanzan bloques hermanos que siguen siendo inequívocos tras esta aceptación.
            for sibling in data['proposals']:
                if (sibling['status'] == 'pending' and sibling['document'] == proposal['document']
                        and sibling['base'] == current['hash'] and sibling['run'] == proposal['run']
                        and sibling['before'] not in proposal['before']
                        and updated.count(sibling['before']) == 1):
                    sibling['base'] = digest(updated)
        proposal['status'] = 'accepted' if accept else 'rejected'
        data['decisions'].append(dict(id=uid(), text=proposal['reason'], status=proposal['status'],
                                     document=proposal['document'], date=time.time(), proposal=proposal_id))
        self.persist(data)
        return self.snapshot(project)
