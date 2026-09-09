#!/usr/bin/env python3
"""Story Workbench — python3 app.py; solo loopback, sin dependencias."""
import argparse
import io
import os
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import urlsplit
import zipfile

from workbench_store import Store, Problem, check, text_value, ROLES, WORKFLOWS, is_link
from workbench_ai import Assistant
from workbench_account import Account
from workbench_voice import Speech
import workbench_modes as modes
from workbench_realtime import Realtime, context as voice_context

WEB = Path(__file__).parent / 'web'


class AppServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, root):
        root = Path(root).absolute()
        check(not any(is_link(p) for p in (root, *root.parents)), 'El directorio de datos no puede ser un enlace.')
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.realtime=Realtime()
        self.instance_fd = os.open(root / '.server.lock', os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            if os.name == 'nt':
                import msvcrt
                try:
                    msvcrt.locking(self.instance_fd, msvcrt.LK_NBLCK, 1)
                except OSError as error:
                    raise BlockingIOError('El directorio ya está abierto.') from error
            else:
                import fcntl
                fcntl.flock(self.instance_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.store = Store(root)
            self.assistant = Assistant(self.store)
            self.account = Account(root)
            self.speech = Speech()
            self.token = secrets.token_urlsafe(32)
            super().__init__(('127.0.0.1', port), Handler)
            self.origin = f'http://127.0.0.1:{self.server_port}'
        except BaseException:
            if self.instance_fd is not None:
                os.close(self.instance_fd)
                self.instance_fd = None
            raise

    def server_close(self):
        super().server_close()
        if self.instance_fd is not None:
            os.close(self.instance_fd)
            self.instance_fd = None



class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # No registrar títulos, rutas privadas, conversaciones ni tokens.

    def send(self, status, payload, content_type='application/json; charset=utf-8'):
        body = json.dumps(payload, ensure_ascii=False).encode() if isinstance(payload, (dict, list)) else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self' wss://generativelanguage.googleapis.com; media-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def gate(self, mutation=False):
        check(self.headers.get('Host') == urlsplit(self.server.origin).netloc, 'Host no permitido.', 403)
        origin = self.headers.get('Origin')
        check(origin is None or origin == self.server.origin, 'Origen no permitido.', 403)
        if mutation:
            check(origin == self.server.origin, 'Se requiere el origen local.', 403)
        token = self.headers.get('Authorization', '')
        check(secrets.compare_digest(token, 'Bearer ' + self.server.token), 'Abrí el enlace completo que muestra la terminal.', 401)

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
            if path in ('/', '/app.js', '/style.css', '/production.js', '/planning.js', '/voice.js', '/voice-capture.js', '/help.js', '/modes.js', '/realtime.js', '/gemini-voice.js'):
                check(self.headers.get('Host') == urlsplit(self.server.origin).netloc, 'Host no permitido.', 403)
                file = WEB / ('index.html' if path == '/' else path[1:])
                self.send(200, file.read_bytes(), mimetypes.guess_type(file)[0] + '; charset=utf-8')
                return
            self.gate()
            store = self.server.store
            with store.lock:
                if path == '/api/realtime':
                    self.send(200,self.server.realtime.status())
                elif path == '/api/voice':
                    self.send(200, self.server.speech.status())
                elif path == '/api/account':
                    self.send(200, self.server.account.snapshot())
                elif path == '/api/projects':
                    self.send(200, {'projects': store.list_projects(), 'active': self.server.assistant.active})
                else:
                    parts = path.strip('/').split('/')
                    check(len(parts) in (3, 4) and parts[:2] == ['api', 'projects'], 'Ruta no encontrada.', 404)
                    project = parts[2]
                    if len(parts) == 3:
                        self.send(200, store.snapshot(project))
                    elif parts[3] in ('book.md', 'book.docx', 'translation.md', 'translation.docx'):
                        from workbench_export import export_book
                        snapshot=store.snapshot(project)
                        if parts[3].startswith('translation.'):
                            snapshot=modes.translation_edition(snapshot)
                        body, mime = export_book(snapshot, 'book.'+parts[3].split('.')[-1])
                        self.send(200, body, mime)
                    elif parts[3] == 'voice-context':
                        self.send(200,voice_context(store.snapshot(project)))
                    elif parts[3] == 'export':
                        data = store.snapshot(project)
                        output = io.BytesIO()
                        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
                            for i, doc in enumerate(data['documents']):
                                # Nombres de entrada controlados; sin traversal ni colisiones.
                                archive.writestr(f'{i+1:02d}-{doc["id"][:8]}.md', doc['content'])
                            archive.writestr('manifest.json', json.dumps({
                                'title': data['title'], 'purpose':data['purpose'], 'translation_config':data.get('translation_config',{}), 'documents': [
                                    {'file': f'{i+1:02d}-{d["id"][:8]}.md', **{k: d[k] for k in ('name', 'role', 'synopsis', 'pov', 'stage', 'translation', 'translation_status') if k in d}}
                                    for i, d in enumerate(data['documents'])], 'word_goal': data.get('word_goal', 0),
                                    'decisions': data['decisions']}, ensure_ascii=False, indent=2))
                        self.send(200, output.getvalue(), 'application/zip')
                    else:
                        raise Problem('Ruta no encontrada.', 404)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as error:
            self.failure(error)

    def do_POST(self):
        try:
            self.gate(True)
            check(self.headers.get('Content-Type', '').split(';')[0] == 'application/json', 'Se requiere JSON.', 415)
            length = int(self.headers.get('Content-Length', '0'))
            check(0 < length <= 2_000_000, 'Solicitud demasiado grande.', 413)
            body = json.loads(self.rfile.read(length))
            check(isinstance(body, dict), 'Solicitud inválida.')
            path = urlsplit(self.path).path
            store = self.server.store
            if path == '/api/realtime/key':
                self.send(200,self.server.realtime.configure(body.get('key'),body.get('provider','openai')))
                return
            if path == '/api/realtime/connect':
                with store.lock:
                    snapshot=store.snapshot(body.get('project'))
                provider=body.get('provider','openai');check(provider in ('openai','gemini'),'Proveedor de voz inválido.')
                result=(self.server.realtime.connect_gemini(snapshot,body.get('consent'),body.get('actions',False)) if provider=='gemini'
                        else self.server.realtime.connect(snapshot,body.get('sdp'),body.get('consent'),body.get('actions',False)))
                self.send(200,result)
                return
            if path == '/api/voice/transcribe':
                self.send(200, self.server.speech.transcribe(body.get('pcm')))
                return
            if path == '/api/voice/read':
                self.send(200, self.server.speech.synthesize(body.get('text')), 'audio/wav')
                return
            if path.startswith('/api/account/'):
                operation = path.rsplit('/', 1)[-1]
                check(operation in ('login', 'refresh', 'logout', 'cancel'), 'Operación inválida.')
                check(not self.server.assistant.active, 'Esperá a que termine la tarea antes de cambiar la sesión.', 409)
                if operation == 'cancel':
                    self.server.account.cancel.set()
                    result = self.server.account.snapshot()
                else:
                    result = self.server.account.start(operation)
                self.send(200, result)
                return
            if path == '/api/quit':
                self.send(200, {'ok': True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            with store.lock:
                if path == '/api/projects':
                    result = store.create(body.get('title'), bool(body.get('demo')),
                                          body.get('workflow', 'writing'), body.get('initial_idea', ''), body.get('purpose','novel'))
                else:
                    project = body.get('project')
                    data = store.load(project)
                    if path == '/api/project/purpose':
                        check(not self.server.assistant.active,'Esperá a que termine la tarea.',409)
                        check(body.get('purpose') in modes.PURPOSES,'Objetivo inválido.')
                        data.update(purpose=body['purpose'],thread=None,context_key=None)
                        if data['purpose']!='novel':data['workflow']='guided'
                        store.persist(data);result=store.snapshot(project)
                    elif path == '/api/translation/config':
                        check(not self.server.assistant.active,'Esperá a que termine la tarea.',409)
                        modes.configure_translation(store,data,body.get('config'));result=store.snapshot(project)
                    elif path == '/api/translation/answer':
                        modes.answer_translation(store,data,body.get('run'),body.get('answer'));result=store.snapshot(project)
                    elif path == '/api/translation/accept':
                        result=modes.accept_translation(store,data,body.get('run'),body.get('text'))
                    elif path == '/api/translation/review':
                        modes.review_translation(store,data,body.get('document'),body.get('hash'),body.get('source_hash'));result=store.snapshot(project)
                    elif path == '/api/project/goal':
                        goal = body.get('goal')
                        check(type(goal) is int and 0 <= goal <= 2_000_000, 'Meta inválida: entre 0 y 2.000.000 palabras.')
                        data['word_goal'] = goal
                        store.persist(data)
                        result = store.snapshot(project)
                    elif path == '/api/project/order':
                        store.reorder(data, body.get('order'))
                        result = store.snapshot(project)
                    elif path == '/api/document/planning':
                        store.planning(data, body.get('document'), body.get('planning'))
                        result = store.snapshot(project)
                    elif path == '/api/run/save-draft':
                        result = store.save_draft(data, body.get('run'))
                    elif path == '/api/project/ai':
                        from workbench_account import ai_preferences, resolve_ai
                        preferences = ai_preferences(body.get('preferences'))
                        resolve_ai(preferences, self.server.account.snapshot().get('models', []))
                        data['ai_preferences'] = preferences
                        store.persist(data)
                        result = store.snapshot(project)
                    elif path == '/api/project/production':
                        from workbench_production import validate_production
                        data['production'] = validate_production(body.get('production'))
                        store.persist(data)
                        result = store.snapshot(project)
                    elif path == '/api/project/workflow':
                        check(body.get('workflow') in WORKFLOWS, 'Forma de trabajo inválida.')
                        data['workflow'] = body['workflow']
                        store.persist(data)
                        result = store.snapshot(project)
                    elif path == '/api/interview/start':
                        check(type(body.get('retry', False)) is bool, 'Reintento inválido.')
                        result = self.server.assistant.start_interview(project, body.get('retry', False))
                    elif path == '/api/document/add':
                        result = store.add_document(project, body.get('name'), body.get('role'), body.get('content'), body.get('selected', True))
                    elif path == '/api/document/save':
                        result = store.save_document(data, body.get('document'), body.get('content'), body.get('hash'))
                    elif path == '/api/document/meta':
                        store.document(data, body.get('document'))
                        doc = next(d for d in data['documents'] if d['id'] == body['document'])
                        if 'selected' in body:
                            check(type(body['selected']) is bool, 'Selección inválida.')
                            doc['selected'] = body['selected']
                        if 'role' in body:
                            check(body['role'] in ROLES, 'Rol inválido.')
                            doc['role'] = body['role']
                        if 'name' in body:
                            doc['name'] = text_value(body['name'], 200, False)
                        store.persist(data)
                        result = store.snapshot(project)
                    elif path == '/api/document/restore':
                        current = store.document(data, body.get('document'))
                        version = next((v for v in current['history'] if v['id'] == body.get('version')), None)
                        check(version is not None, 'Versión no encontrada.', 404)
                        content = store.path(project, 'history', version['id'] + '.md').read_text(encoding='utf-8')
                        result = store.save_document(data, current['id'], content, body.get('hash'), 'Restauración de versión')
                    elif path == '/api/proposal/decide':
                        check(type(body.get('accept')) is bool, 'Decisión inválida.')
                        result = store.decide(project, body.get('proposal'), body['accept'])
                    elif path == '/api/decision':
                        check(body.get('status') in ('accepted', 'pending', 'rejected'), 'Estado inválido.')
                        from workbench_store import uid
                        import time
                        data['decisions'].append(dict(id=uid(), text=text_value(body.get('text'), 4000, False),
                                                      status=body['status'], date=time.time()))
                        store.persist(data)
                        result = store.snapshot(project)
                    elif path == '/api/thread/reset':
                        check(not self.server.assistant.active, 'Esperá a que termine la tarea.', 409)
                        data.update(thread=None, context_key=None)
                        store.persist(data)
                        result = store.snapshot(project)
                    elif path == '/api/run':
                        result = self.server.assistant.start(project, body.get('mode'),
                            text_value(body.get('prompt'), 10_000, False), body.get('skill', True))
                    elif path == '/api/run/cancel':
                        self.server.assistant.stop(project, body.get('run'))
                        result = {'ok': True}
                    else:
                        raise Problem('Ruta no encontrada.', 404)
            self.send(200, result)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as error:
            self.failure(error)

    def failure(self, error):
        if isinstance(error, Problem):
            self.send(error.status, {'error': str(error)})
        elif isinstance(error, (ValueError, TypeError, UnicodeError)):
            self.send(400, {'error': 'Datos inválidos.'})
        else:
            self.send(500, {'error': 'No se pudo completar la operación local. Tu borrador sigue en el editor.'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).parent / 'private' / 'workbench')
    args = parser.parse_args()
    server = AppServer(args.port, args.data_dir)
    if os.environ.get('STORY_DESKTOP'):
        print(json.dumps({'origin': server.origin, 'token': server.token}), flush=True)
        def watch_parent():
            sys.stdin.read()
            server.shutdown()
        threading.Thread(target=watch_parent, daemon=True).start()
    print(f'Story Workbench · Abrí {server.origin}/#token={server.token}', flush=True)
    print('Datos privados locales. Ctrl+C para detener.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.account.cancel.set()
        server.assistant.cancel.set()
        if server.assistant.thread:
            server.assistant.thread.join(timeout=12)
        if server.account.thread:
            server.account.thread.join(timeout=8)
        server.server_close()
