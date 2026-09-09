"""Login administrado por Codex. Nunca devuelve tokens ni datos de la cuenta al navegador."""
import asyncio
from pathlib import Path
import threading
from urllib.parse import urlsplit

from scripts.codex_smoke import Server, chatgpt_only
from workbench_store import check, is_link


def auth_url(value):
    url = urlsplit(value)
    check(url.scheme == 'https' and url.hostname == 'auth.openai.com'
          and url.port in (None, 443) and not url.username and not url.password,
          'Codex devolvió una dirección de inicio de sesión inesperada.')
    return value


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

    async def execute(self, operation):
        async with Server(self.cwd, require_account=False) as server:
            if operation == 'logout':
                await server.rpc('account/logout', {})
                self.set(status='signed_out')
                return
            result = await server.rpc('account/read', {'refreshToken': False})
            if (result.get('account') or {}).get('type') == 'chatgpt':
                self.set(status='connected')
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
                            self.set(status='connected')
                            return
            finally:
                if self.snapshot()['status'] != 'connected':
                    await server.rpc('account/login/cancel', {'loginId': login['loginId']})
                    self.set(status='signed_out')
