"""Login administrado por Codex. Nunca devuelve tokens ni datos de la cuenta al navegador."""
import asyncio
from pathlib import Path
import threading
from urllib.parse import urlsplit

from scripts.codex_smoke import Server, chatgpt_only
from src.workbench_store import check, is_link


def auth_url(value):
    url = urlsplit(value)
    check(url.scheme == 'https' and url.hostname == 'auth.openai.com'
          and url.port in (None, 443) and not url.username and not url.password,
          'Codex devolvió una dirección de inicio de sesión inesperada.')
    return value


async def list_models(server):
    models, cursor, visited = [], None, set()
    while True:
        result = await server.rpc('model/list', {'includeHidden': False, 'limit': 100, 'cursor': cursor})
        for model in result['data']:
            if not model.get('hidden') and 'text' in model.get('inputModalities', ['text']):
                models.append({key: model[key] for key in ('model', 'displayName', 'isDefault',
                               'defaultReasoningEffort', 'supportedReasoningEfforts')})
        cursor = result.get('nextCursor')
        if not cursor:
            return models
        check(cursor not in visited and len(models) < 1000, 'No se pudo completar el catálogo de modelos.')
        visited.add(cursor)


def ai_preferences(value):
    check(isinstance(value, dict), 'Selección de IA inválida.')
    result = {key: value.get(key) for key in ('model', 'effort')}
    for key, value in result.items():
        check(value is None or (isinstance(value, str) and 0 < len(value) <= 160
              and all(c.isalnum() or c in '-_.' for c in value)), 'Selección de IA inválida.')
    return result


def resolve_ai(preferences, models):
    preferences = ai_preferences(preferences)
    check(models, 'No se encontraron modelos. Actualizá la conexión con ChatGPT.')
    model = next((m for m in models if m['model'] == preferences['model']), None) if preferences['model'] else next((m for m in models if m['isDefault']), models[0])
    check(model, 'El modelo elegido ya no está disponible. Elegí otro explícitamente.')
    efforts = [e['reasoningEffort'] for e in model['supportedReasoningEfforts']]
    effort = preferences['effort'] or ('medium' if 'medium' in efforts else model['defaultReasoningEffort'])
    check(effort in efforts, 'Ese esfuerzo no está disponible para el modelo elegido.')
    return {'model': model['model'], 'effort': effort}


class Account:
    def __init__(self, root):
        self.cwd = Path(root) / 'account'
        check(not is_link(self.cwd), 'No se permiten enlaces en la carpeta de conexión.')
        self.cwd.mkdir(exist_ok=True, mode=0o700)
        self.state = {'status': 'unknown'}
        self.lock = threading.Lock()
        self.cancel = threading.Event()
        self.thread = None

    def snapshot(self):
        with self.lock:
            return dict(self.state)

    def set(self, **state):
        with self.lock:
            self.state = state

    def start(self, operation):
        with self.lock:
            check(not self.thread or not self.thread.is_alive(), 'Ya hay una conexión en curso.', 409)
            self.cancel.clear()
            self.state = {'status': 'checking'}
            self.thread = threading.Thread(target=self.worker, args=(operation,), daemon=True)
            self.thread.start()
        return self.snapshot()

    def worker(self, operation):
        try:
            asyncio.run(self.execute(operation))
        except Exception:
            self.set(status='error', error='No se pudo conectar. Revisá tu conexión y volvé a intentar. No se usó API de pago.')

    async def connected(self, server):
        try:
            self.set(status='connected', models=await list_models(server))
        except Exception:
            self.set(status='connected', models=[], models_error='No se pudo cargar el catálogo. Usá Actualizar modelos para reintentar.')

    async def execute(self, operation):
        async with Server(self.cwd, require_account=False) as server:
            if operation == 'logout':
                await server.rpc('account/logout', {})
                self.set(status='signed_out')
                return
            result = await server.rpc('account/read', {'refreshToken': False})
            if (result.get('account') or {}).get('type') == 'chatgpt':
                await self.connected(server)
                return
            if operation == 'refresh':
                self.set(status='signed_out')
                return
            login = await server.rpc('account/login/start', {'type': 'chatgpt'})
            check(login['type'] == 'chatgpt', 'Se requiere ChatGPT.')
            self.set(status='waiting', url=auth_url(login['authUrl']))
            try:
                async with asyncio.timeout(180):
                    while not self.cancel.is_set():
                        try:
                            event = server.events.pop(0) if server.events else await asyncio.wait_for(server.read(), .25)
                        except asyncio.TimeoutError:
                            continue
                        if event.get('method') == 'account/login/completed':
                            params = event['params']
                            if params.get('loginId') != login['loginId']:
                                continue
                            check(params.get('success'), 'No se completó el inicio de sesión.')
                            chatgpt_only(await server.rpc('account/read', {'refreshToken': False}))
                            await self.connected(server)
                            return
            finally:
                if self.snapshot()['status'] != 'connected':
                    await server.rpc('account/login/cancel', {'loginId': login['loginId']})
                    self.set(status='signed_out')
