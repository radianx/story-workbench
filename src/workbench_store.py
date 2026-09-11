"""Archivos Markdown privados y metadatos locales; sin dependencias."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import time
import uuid

MAX_TEXT = 1_000_000  # UTF-8 storage bound, not a model context or translation-unit limit.
WORKFLOWS = ('writing', 'guided')
ROLES = ('manuscrito', 'canon', 'estilo', 'referencia', 'plan', 'traducción')
STAGES = ('planned', 'drafting', 'revise', 'reviewed')


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


def is_link(path):
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def atomic(path, text):
    check(not is_link(path), 'No se permiten enlaces simbólicos.')
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.save-')
    try:
        with os.fdopen(fd, 'wb' if isinstance(text, bytes) else 'w', **({} if isinstance(text, bytes) else {'encoding': 'utf-8', 'newline': ''})) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
        if os.name != 'nt':
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
        check(not any(is_link(p) for p in (self.root, *self.root.parents)),
              'El directorio de datos no puede ser un enlace.')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        for project in self.list_projects(archived=None):
            data = self.load(project['id'])
            changed = False
            for run in data['runs']:
                if run['status'] in ('running', 'connecting', 'cancelling'):
                    run.update(status='interrupted', error='El servicio se reinició. Podés volver a pedir la tarea.')
                    for worker in run.get('team_workers',[]):
                        if worker['status'] in ('connecting','running'):worker['status']='interrupted'
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
        check(not any(is_link(p) for p in (path, *path.parents)), 'No se permiten enlaces simbólicos.')
        check(path.is_relative_to(self.root), 'Ruta fuera del proyecto.')
        return path

    def list_projects(self, archived=False):
        projects = []
        for path in self.root.iterdir():
            if re.fullmatch('[a-f0-9]{32}', path.name):
                data = self.load(path.name)
                hidden = bool(data.get('archived', False))
                if archived is None or hidden == archived:
                    projects.append({**{k: data[k] for k in ('id', 'title', 'updated')}, 'archived': hidden})
        return sorted(projects, key=lambda p: p['updated'], reverse=True)

    def archive_project(self, data, archived):
        check(type(archived) is bool, 'Estado de archivo inválido.')
        check(not archived or not any(r['status'] in ('running','connecting','cancelling') for r in data['runs']),
              'Esperá a que termine la tarea antes de archivar el proyecto.',409)
        if bool(data.get('archived',False)) != archived:
            data['archived'] = archived
            self.persist(data)

    def load(self, project):
        path = self.path(project, 'project.json')
        check(path.is_file(), 'Proyecto no encontrado.', 404)
        data = json.loads(path.read_text(encoding='utf-8'))
        from src.workbench_migrations import migrate_project
        data = migrate_project(data)
        return data

    def reset_conversation(self, data, draft=''):
        check(not any(r['status'] in ('connecting','running','cancelling') for r in data['runs']),
              'Esperá a que termine la tarea.',409)
        text_value(draft,10_000)
        start,end=data.get('history_start',0),len(data['runs'])
        if start<end or draft.strip():
            title=data['runs'][start]['prompt'] if start<end else draft
            data['conversations'].append(dict(id=uid(),title=' '.join(title.split())[:90],
                start=start,end=end,date=time.time(),draft=draft))
        data.update(thread=None,context_key=None,history_start=end)
        self.persist(data)

    def persist(self, data):
        from src.workbench_migrations import migrate_project
        data.update(migrate_project(data))
        data['updated'] = time.time()
        atomic(self.path(data['id'], 'project.json'), json.dumps(data, ensure_ascii=False))

    def create(self, title, demo=False, workflow='writing', initial_idea='', purpose='novel', documents=None, translation=None):
        from src.workbench_modes import PURPOSES, translation_languages, configure_translation
        check(purpose in PURPOSES, 'Objetivo de proyecto inválido.')
        check(not demo or purpose=='novel', 'El ejemplo es un proyecto de historia.')
        text_value(title, 160, False)
        check(workflow in WORKFLOWS, 'Forma de trabajo inválida.')
        text_value(initial_idea, 6000)
        check(not demo or workflow == 'writing', 'El ejemplo se abre en modo escritura.')
        documents = [] if documents is None else documents
        check(isinstance(documents,list) and len(documents)<=100 and not (demo and documents), 'Documentos iniciales inválidos.')
        prepared = []
        for doc in documents:
            check(isinstance(doc,dict), 'Documento inválido.')
            name=text_value(doc.get('name'),200,False)
            content=text_value(doc.get('content'))
            role=doc.get('role','referencia');check(role in ROLES and role!='traducción', 'Rol de original inválido.')
            prepared.append(dict(name=name,content=content,role=role,selected=False))
        config = None
        if purpose == 'translation':
            config=translation_languages(translation)
            index=translation.get('source')
            check(type(index) is int and 0<=index<len(prepared), 'Importá una obra existente y elegí el original.')
            original=prepared[index];text_value(original['content'],empty=False)
            original.update(role='manuscrito', selected=True)
            workflow='guided';initial_idea=''
        project = uid()
        path = self.path(project)
        path.mkdir(mode=0o700)
        for name in ('documents', 'history', 'agent'):
            (path / name).mkdir(mode=0o700)
        data = dict(id=project, title=title, updated=time.time(), documents=[], proposals=[],
                    decisions=[], runs=[], thread=None, context_key=None,
                    workflow=workflow, initial_idea=initial_idea, purpose=purpose)
        try:
            self.persist(data)
            for doc in prepared:
                self.add_document(project, **doc)
            if config:
                data=self.load(project)
                configure_translation(self,data,{**config,'source':data['documents'][index]['id']})
        except BaseException:
            shutil.rmtree(path)
            raise
        if demo:
            examples = [
                ('01 · La última luz.md', 'manuscrito', '# La última luz\n\nInés dejó la llave azul sobre la mesa del faro. Afuera, el agua borraba el camino.\n\n—Mi padre vuelve el viernes —dijo.\n\nTomás miró el calendario. Era jueves. Hacía tres años que habían enterrado a Julián.\n\nLa radio crujió. Inés reconoció la voz antes de escuchar su nombre.\n'),
                ('Canon del faro.md', 'canon', '# Canon aprobado\n\n- Inés tiene veintinueve años.\n- Su padre, Julián, murió hace tres años.\n- La llave del cuarto de radio es roja.\n- Tomás no conoce la voz de Julián.\n\n# Idea provisional\n\nLa transmisión podría ser una grabación. No está decidido.\n'),
                ('Voz y tono.md', 'estilo', '# Voz y tono\n\nTercera persona cercana a Inés. Pasado. Diálogos breves con voseo.\nConservar la incertidumbre sobre la radio. No explicar aún su origen.\nEvitar convertir las imágenes en explicaciones.\n'),
                ('02 · El cuarto de radio.md', 'manuscrito', '# El cuarto de radio\n\nInés giró la llave roja. Tomás esperó al otro lado de la puerta.\n\nLa voz volvió a llamarla. Ella no contestó.\n')]
            for name, role, content in examples:
                self.add_document(project, name, role, content)
        elif workflow == 'writing' and purpose=='novel' and not prepared:
            self.add_document(project, 'Manuscrito.md', 'manuscrito', '')
        return self.load(project)

    def document(self, data, document):
        found = next((d for d in data['documents'] if d['id'] == document), None)
        check(found is not None, 'Documento no encontrado.', 404)
        path = self.path(data['id'], 'documents', found['id'] + '.md')
        check(path.stat().st_size <= MAX_TEXT, 'Documento demasiado grande.')
        content = path.read_bytes().decode('utf-8')
        result = {**found, 'content': content, 'hash': digest(content)}
        if result.get('stage') == 'reviewed' and result.get('review_hash') != result['hash']:
            result['stage'] = 'revise'
        if result.get('translation'):
            from src.workbench_modes import translation_status
            result['translation_status']=translation_status(self,data,result)
        return result

    def snapshot(self, project):
        data = self.load(project)
        data['documents'] = [self.document(data, d['id']) for d in data['documents']]
        # Los snapshots de contexto quedan privados; la UI recibe referencias, no duplicados completos.
        for run in data['runs']:
            run.pop('source_texts', None)
        return data

    def add_documents(self, data, documents):
        check(isinstance(documents, list) and documents and len(data['documents']) + len(documents) <= 100,
              'La biblioteca admite hasta 100 documentos por proyecto.')
        prepared = []
        for item in documents:
            check(isinstance(item, dict), 'Documento inválido.')
            name = text_value(item.get('name'), 200, False)
            content = text_value(item.get('content'), empty=False)
            role = item.get('role', 'referencia')
            check(role in ROLES and role != 'traducción', 'Rol de original inválido.')
            prepared.append((dict(id=uid(), name=name, role=role, selected=False, history=[]), content))
        written = []
        previous = list(data['documents'])
        try:
            for document, content in prepared:
                path = self.path(data['id'], 'documents', document['id'] + '.md')
                atomic(path, content)
                written.append(path)
                data['documents'].append(document)
            self.persist(data)
        except Exception:
            committed = {d['id'] for d in self.load(data['id'])['documents']}
            data['documents'] = previous
            for path in written:
                if path.stem not in committed:
                    path.unlink(missing_ok=True)
            raise

    def add_document(self, project, name, role, content, selected=True, source_run=None, translation=None):
        text_value(name, 200, False)
        text_value(content)
        check(role in ROLES, 'Rol inválido.')
        check(type(selected) is bool, 'Selección inválida.')
        data = self.load(project)
        check(len(data['documents']) < 100, 'Límite del prototipo: 100 documentos por proyecto.')
        document = dict(id=uid(), name=name, role=role, selected=selected, history=[])
        if translation:
            document['translation']=translation
        if source_run:
            document['source_run'] = source_run
        atomic(self.path(project, 'documents', document['id'] + '.md'), content)
        data['documents'].append(document)
        self.persist(data)
        return self.document(data, document['id'])

    def planning(self, data, document, values):
        current = self.document(data, document)
        check(current['role'] == 'manuscrito', 'El plan organiza documentos de manuscrito.')
        check(isinstance(values, dict), 'Ficha inválida.')
        stage = values.get('stage', 'planned')
        check(stage in STAGES, 'Estado editorial inválido.')
        check(stage != 'reviewed' or bool(current['content'].strip()), 'Un documento vacío no puede estar revisado.')
        check(values.get('hash') == current['hash'], 'El texto cambió. Volvé a abrir el plan antes de marcar su estado.', 409)
        prepared = dict(synopsis=text_value(values.get('synopsis', ''), 4000),
                        pov=text_value(values.get('pov', ''), 200), stage=stage,
                        review_hash=current['hash'] if stage == 'reviewed' else None)
        next(d for d in data['documents'] if d['id'] == document).update(prepared)
        self.persist(data)

    def reorder(self, data, order):
        manuscripts = {d['id']: d for d in data['documents'] if d['role'] == 'manuscrito'}
        check(isinstance(order, list) and all(isinstance(i, str) for i in order)
              and len(order) == len(manuscripts) and set(order) == set(manuscripts),
              'El listado cambió o contiene documentos inválidos. Volvé a abrir el plan.', 409)
        ordered = iter(manuscripts[i] for i in order)
        data['documents'] = [next(ordered) if d['role'] == 'manuscrito' else d for d in data['documents']]
        self.persist(data)

    def save_draft(self, data, run_id):
        run = next((r for r in data['runs'] if r['id'] == run_id), None)
        check(run is not None and run['mode'] == 'draft' and run['status'] == 'completed', 'Borrador no disponible.', 409)
        if run.get('saved_document'):
            return self.document(data, run['saved_document'])
        existing = next((d for d in data['documents'] if d.get('source_run') == run_id), None)
        document = (self.document(data, existing['id']) if existing else
                    self.add_document(data['id'], 'Material de rol provisional.md' if run.get('purpose')=='rpg' else 'Borrador provisional.md', 'plan' if run.get('purpose')=='rpg' else 'manuscrito', run['text'], selected=run.get('purpose')!='rpg', source_run=run_id))
        # Recargar: add_document ya guardó los metadatos del nuevo documento.
        data = self.load(data['id'])
        next(r for r in data['runs'] if r['id'] == run_id)['saved_document'] = document['id']
        self.persist(data)
        return document

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
