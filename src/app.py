#!/usr/bin/env python3
"""Story Workbench — python3 -m src.app; solo loopback."""
import argparse
import os
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import urlsplit

from src.workbench_store import Store, Problem, check, is_link
from src.workbench_ai import Assistant
from src.workbench_account import Account
from src.workbench_voice import Speech
import src.workbench_modes as modes
from src.workbench_workspace import Workspace
from src.workbench_realtime import Realtime, context as voice_context

from src.workbench_operations import project_operation
from src.workbench_images import Images
from src import ROOT

WEB = ROOT / 'web'


class AppServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, root):
        self.workspace = Workspace(root)
        root = self.workspace.active
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
            self.images = Images(lambda provider: self.assistant.providers.keys.get(provider) or (self.realtime.gemini_key if provider == 'gemini' else self.realtime.key))
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
        if self.realtime.reading:self.realtime.reading.cancel()
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
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self' wss://generativelanguage.googleapis.com wss://api.openai.com/v1/realtime; media-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
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
            if path in ('/', '/appearance.js', '/app.js', '/markdown-it.min.js', '/markdown.js', '/style.css', '/production.js', '/planning.js', '/voice.js', '/voice-capture.js', '/help.js', '/modes.js', '/realtime.js', '/gemini-voice.js', '/settings.js', '/setup.js', '/providers.js', '/team.js', '/bootstrap.js', '/images.js', '/formats.js'):
                check(self.headers.get('Host') == urlsplit(self.server.origin).netloc, 'Host no permitido.', 403)
                file = WEB / ('index.html' if path == '/' else path[1:])
                self.send(200, file.read_bytes(), mimetypes.guess_type(file)[0] + '; charset=utf-8')
                return
            self.gate()
            store = self.server.store
            with store.lock:
                if path == '/api/images/providers':
                    self.send(200, self.server.images.status())
                elif path == '/api/workspace':
                    self.send(200,self.server.workspace.status())
                elif path in ('/api/voice-storage','/api/engine-storage'):
                    self.send(200,dict(available=False,stored={},reason='El guardado seguro está disponible en la app de escritorio con un almacén de claves del sistema.'))
                elif path == '/api/engines':
                    self.send(200,self.server.assistant.providers.status())
                elif path == '/api/realtime':
                    self.send(200,self.server.realtime.status())
                elif path == '/api/voice':
                    self.send(200, self.server.speech.status())
                elif path == '/api/account':
                    self.send(200, self.server.account.snapshot())
                elif path == '/api/projects':
                    projects=store.list_projects(archived=None)
                    self.send(200, {'projects': [p for p in projects if not p['archived']],
                                    'archived': [p for p in projects if p['archived']], 'active': self.server.assistant.active})
                else:
                    parts = path.strip('/').split('/')
                    check(len(parts) in (3, 4, 5) and parts[:2] == ['api', 'projects'], 'Ruta no encontrada.', 404)
                    project = parts[2]
                    if len(parts) == 5:
                        check(parts[3] == 'images', 'Ruta no encontrada.', 404)
                        data = store.load(project)
                        record = next((item for item in data.get('images', []) if item['id'] == parts[4]), None)
                        check(record is not None, 'Imagen no encontrada.', 404)
                        check(record['mime'] in ('image/png', 'image/jpeg'), 'Imagen inválida.')
                        raw = store.path(project, 'images', record['file']).read_bytes()
                        if urlsplit(self.path).query == 'thumbnail=1':
                            import io
                            from PIL import Image
                            with Image.open(io.BytesIO(raw)) as image:
                                image.thumbnail((480, 360))
                                output = io.BytesIO()
                                image.save(output, format='PNG')
                                raw = output.getvalue()
                            self.send(200, raw, 'image/png')
                        else:
                            self.send(200, raw, record['mime'])
                    elif len(parts) == 3:
                        self.send(200, store.snapshot(project))
                    elif parts[3] in ('book.md', 'book.docx', 'book.pdf', 'translation.md', 'translation.docx', 'translation.pdf'):
                        from src.workbench_export import export_book
                        snapshot=store.snapshot(project)
                        if parts[3].startswith('translation.'):
                            snapshot=modes.translation_edition(snapshot)
                        body, mime = export_book(snapshot, 'book.'+parts[3].split('.')[-1])
                        self.send(200, body, mime)
                    elif parts[3] == 'voice-context':
                        self.send(200,voice_context(store.snapshot(project)))
                    elif parts[3] == 'export':
                        from src.workbench_export import export_project
                        body, mime = export_project(store, project)
                        self.send(200, body, mime)
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
            check(0 < length <= (40_000_000 if urlsplit(self.path).path in ('/api/import/file', '/api/projects', '/api/document/import') else 8_000_000), 'Solicitud demasiado grande.', 413)
            body = json.loads(self.rfile.read(length))
            check(isinstance(body, dict), 'Solicitud inválida.')
            path = urlsplit(self.path).path
            store = self.server.store
            if path.startswith('/api/images/'):
                operation = path.rsplit('/', 1)[-1]
                check(operation in ('start', 'poll', 'cancel', 'save'), 'Operación inválida.', 404)
                with store.lock:
                    project = store.load(body.get('project'))['id']
                images = self.server.images
                if operation == 'start':
                    result = images.start(project, body)
                elif operation == 'save':
                    result = images.save(store, project, body.get('id'))
                elif operation == 'cancel':
                    result = images.cancel(body.get('id'), project)
                else:
                    result = images.snapshot(body.get('id'), project)
                self.send(200, result)
                return
            if path == '/api/import/file':
                from src.workbench_import import import_file
                self.send(200, import_file(body.get('name'), body.get('data')))
                return
            if path in ('/api/voice-storage','/api/engine-storage'):
                raise Problem('El guardado seguro requiere la app de escritorio y el almacén del sistema.')
            if path == '/api/engine/key':
                check(not self.server.assistant.active, 'Esperá a que termine la tarea antes de cambiar la clave.',409)
                self.send(200,self.server.assistant.providers.configure(body.get('provider'),body.get('key')))
                return
            if path == '/api/realtime/key':
                self.send(200,self.server.realtime.configure(body.get('key'),body.get('provider','openai')))
                return
            if path == '/api/realtime/connect':
                with store.lock:
                    snapshot=store.snapshot(body.get('project'))
                provider=body.get('provider','openai');check(provider in ('openai','gemini'),'Proveedor de voz inválido.')
                relay=body.get('relay',False);check(type(relay) is bool,'Modo de voz inválido.')
                options={'relay':True} if relay else {}
                result=(self.server.realtime.connect_gemini(snapshot,body.get('consent'),body.get('actions',False),**options) if provider=='gemini'
                        else self.server.realtime.connect(snapshot,body.get('sdp'),body.get('consent'),body.get('actions',False),**options))
                self.send(200,result)
                return
            if path == '/api/realtime/speech':
                self.send(200,self.server.realtime.speech(body))
                return
            if path == '/api/realtime/read-session':
                self.send(200,self.server.realtime.read_session(body.get('provider'),body.get('consent')))
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
            result = project_operation(self.server, path, body)
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
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'private' / 'workbench')
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
