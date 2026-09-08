#!/usr/bin/env python3
"""Prueba stdio con cuenta ChatGPT. Python 3.11+, sin dependencias."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import tempfile
import tomllib


class SmokeError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise SmokeError(message)


def chatgpt_only(result):
    require((result.get('account') or {}).get('type') == 'chatgpt',
            'Se requiere login ChatGPT administrado por Codex. No se usará API.')


def launch_settings():
    home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    config_path = home / 'config.toml'
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    require('openai' not in config.get('model_providers', {}),
            'Proveedor openai personalizado: revisar antes de ejecutar.')
    overrides = {
        'forced_login_method': 'chatgpt', 'model_provider': 'openai',
        'approval_policy': 'never', 'sandbox_mode': 'read-only',
        'approvals_reviewer': 'user', 'features.memories': False,
        'features.multi_agent': False, 'features.apps': False,
        'web_search': 'disabled', 'model_reasoning_effort': 'low',
    }
    for section in ('mcp_servers', 'plugins'):
        for name in config.get(section, {}):
            overrides[f'{section}.{name}.enabled'] = False
    command = ['codex', 'app-server', '--listen', 'stdio://']
    for key, value in overrides.items():
        command += ['-c', f'{key}={json.dumps(value)}']
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('OPENAI_', 'AZURE_OPENAI_', 'CODEX_API_', 'CODEX_THREAD_'))}
    return command, env


class Server:
    # ponytail: un solo consumidor y una petición en vuelo; multiplexar para el editor.
    async def __aenter__(self):
        command, env = launch_settings()
        self.process = await asyncio.create_subprocess_exec(
            *command, env=env, cwd=self.cwd, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            limit=8 * 1024 * 1024)
        self.sequence = 0
        self.events = []
        try:
            await self.rpc('initialize', {'clientInfo': {
                'name': 'story_workbench_smoke', 'version': '0.1.0'}})
            await self.send({'method': 'initialized', 'params': {}})
            chatgpt_only(await self.rpc('account/read', {'refreshToken': False}))
        except BaseException:
            await self.__aexit__(None, None, None)
            raise
        print('OK initialize + cuenta ChatGPT', flush=True)
        return self

    def __init__(self, cwd):
        self.cwd = str(cwd)

    async def __aexit__(self, *_):
        if self.process.returncode is None:
            self.process.stdin.close()
            try:
                await asyncio.wait_for(self.process.wait(), 5)
            except asyncio.TimeoutError:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), 5)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()

    async def send(self, message):
        self.process.stdin.write((json.dumps(message) + '\n').encode())
        await self.process.stdin.drain()

    async def read(self):
        line = await self.process.stdout.readline()
        require(bool(line), 'App Server cerró stdout; revisar instalación/permisos.')
        message = json.loads(line)
        if 'method' in message and 'id' in message:
            method = message['method']
            if method in ('item/commandExecution/requestApproval',
                          'item/fileChange/requestApproval'):
                await self.send({'id': message['id'], 'result': {'decision': 'decline'}})
            else:
                await self.send({'id': message['id'], 'error': {
                    'code': -32601, 'message': 'No admitido en esta prueba'}})
        return message

    async def rpc(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        await self.send({'id': request_id, 'method': method, 'params': params})
        async with asyncio.timeout(45):
            while True:
                message = await self.read()
                if message.get('id') == request_id and 'method' not in message:
                    require('error' not in message,
                            f'{method}: error RPC (sin mostrar datos de cuenta).')
                    return message['result']
                self.events.append(message)

    async def finish(self, thread_id, turn_id):
        deltas, items = [], []
        async with asyncio.timeout(180):
            while True:
                event = self.events.pop(0) if self.events else await self.read()
                p = event.get('params', {})
                if p.get('threadId') != thread_id:
                    continue
                method = event.get('method')
                if method == 'turn/completed' and p['turn']['id'] == turn_id:
                    status = p['turn']['status']
                    if status not in ('completed', 'interrupted'):
                        info = (p['turn'].get('error') or {}).get('codexErrorInfo')
                        reasons = {
                            'usageLimitExceeded': 'límite de uso alcanzado',
                            'rateLimitExceeded': 'límite de solicitudes alcanzado',
                            'unauthorized': 'sesión no autorizada',
                            'contextWindowExceeded': 'contexto excedido',
                            'sandboxError': 'error de sandbox',
                        }
                        reason = reasons.get(info, 'conexión o proveedor') if isinstance(info, str) else 'conexión o proveedor'
                        raise SmokeError(f'Turno fallido: {reason}. Sin fallback API.')
                    return status, ''.join(deltas), items
                if p.get('turnId') != turn_id:
                    continue
                if method == 'item/agentMessage/delta':
                    deltas.append(p['delta'])
                if method == 'item/completed':
                    items.append(p['item'])

    async def wait_for_delta(self, thread_id, turn_id):
        # turn/start puede responder antes de que exista un turno interrumpible.
        pending, self.events = self.events, []
        async with asyncio.timeout(180):
            while True:
                event = pending.pop(0) if pending else await self.read()
                self.events.append(event)
                p = event.get('params', {})
                if p.get('threadId') != thread_id:
                    continue
                if event.get('method') == 'turn/completed' and p['turn']['id'] == turn_id:
                    raise SmokeError('El turno terminó antes de poder probar cancelación.')
                if (event.get('method') == 'item/agentMessage/delta'
                        and p.get('turnId') == turn_id):
                    self.events.extend(pending)
                    return

    async def turn(self, thread_id, text, skill=None):
        inputs = [{'type': 'text', 'text': text}]
        if skill:
            inputs.append({'type': 'skill', 'name': 'build-novel', 'path': skill})
        response = await self.rpc('turn/start', {
            'threadId': thread_id, 'input': inputs,
            'sandboxPolicy': {'type': 'readOnly', 'networkAccess': False},
            'approvalPolicy': 'never', 'effort': 'low'})
        return response['turn']['id']


async def smoke():
    with tempfile.TemporaryDirectory(prefix='story-workbench-smoke-') as directory:
        cwd = Path(directory)
        scene = cwd / 'scene.md'
        original = b'# Prueba ficticia\nInes guarda una llave azul en el faro.\n'
        scene.write_bytes(original)
        policy = {'cwd': directory, 'sandbox': 'read-only', 'approvalPolicy': 'never',
                  'approvalsReviewer': 'user', 'modelProvider': 'openai',
                  'developerInstructions':
                  'Prueba técnica con texto ficticio. No busques libros ni otros proyectos. '
                  'Solo puedes leer scene.md y la skill build-novel con sus referencias. '
                  'No uses subagentes, conectores, red, memorias ni publicaciones. '
                  'No ejecutes scripts de la skill ni crees estructura editorial. '
                  'No reescribas el texto. Responde breve y en español.'}
        try:
            async with Server(cwd) as server:
                skills = await server.rpc('skills/list', {'cwds': [directory], 'forceReload': True})
                matches = [s for group in skills['data'] for s in group['skills']
                           if s['name'] == 'build-novel' and s.get('enabled')]
                require(len(matches) == 1, 'build-novel no disponible o ambiguo; no se copiará.')
                skill = matches[0]['path']
                require(Path(skill).is_file(), 'La skill anunciada no existe.')
                print('OK build-novel descubierto (instalación local, sin redistribuir)', flush=True)
                result = await server.rpc('thread/start', policy)
                require(result['modelProvider'] == 'openai', 'Proveedor inesperado.')
                require(result['sandbox']['type'] == 'readOnly', 'Sandbox inesperado.')
                thread_id = result['thread']['id']
                probe = await server.rpc('command/exec', {
                    'command': ['python3', '-c',
                        "import errno\nfrom pathlib import Path\n"
                        "assert 'azul' in Path('scene.md').read_text()\n"
                        "try:\n Path('write-probe.txt').write_text('probe')\n"
                        "except OSError as e:\n assert e.errno in (errno.EACCES, errno.EPERM, errno.EROFS)\n print('WRITE_DENIED')\n"
                        "else:\n raise SystemExit(9)"],
                    'cwd': directory, 'timeoutMs': 10000,
                    'sandboxPolicy': {'type': 'readOnly', 'networkAccess': False}})
                require(probe['exitCode'] == 0 and 'WRITE_DENIED' in probe['stdout'],
                        'No se verificó lectura permitida y escritura bloqueada.')
                print('OK sandbox: lectura permitida, escritura bloqueada', flush=True)
                turn_id = await server.turn(thread_id,
                    'Usa $build-novel. Lee scene.md y devuelve un diagnóstico de una frase, '
                    'sin reescribir ni guardar. Recuerda la clave ficticia FARO-731 '
                    'solo en esta conversación. Menciona la clave y el color de la llave.', skill)
                status, streamed, items = await server.finish(thread_id, turn_id)
                require(status == 'completed' and 'FARO-731' in streamed and 'azul' in streamed.lower(),
                        'No se verificó respuesta en streaming con el contexto ficticio.')
                print('OK turno + streaming + contexto ficticio', flush=True)
                turn_id = await server.turn(thread_id,
                    'Enumera 200 ideas ficticias para faros, una por línea. No uses herramientas.')
                await server.wait_for_delta(thread_id, turn_id)
                await server.rpc('turn/interrupt', {'threadId': thread_id, 'turnId': turn_id})
                status, _, _ = await server.finish(thread_id, turn_id)
                require(status == 'interrupted', 'No se confirmó cancelación del turno.')
                print('OK cancelación confirmada', flush=True)
            async with Server(cwd) as server:
                result = await server.rpc('thread/resume', {**policy, 'threadId': thread_id})
                require(result['thread']['id'] == thread_id, 'Se reanudó otro hilo.')
                turn_id = await server.turn(thread_id,
                    'Sin herramientas: ¿qué clave ficticia y color de llave recordás? Una frase.')
                status, streamed, _ = await server.finish(thread_id, turn_id)
                require(status == 'completed' and 'FARO-731' in streamed and 'azul' in streamed.lower(),
                        'No se recuperó el contexto tras reiniciar App Server.')
                print('OK reanudación tras reinicio + recuerdo del contexto', flush=True)
        finally:
            require(scene.read_bytes() == original, 'El documento ficticio fue alterado.')
            require(sorted(p.name for p in cwd.iterdir()) == ['scene.md'],
                    'Se crearon archivos inesperados en el proyecto ficticio.')
            print('OK documento ficticio intacto', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Usar la sesión ChatGPT y su cuota.')
    args = parser.parse_args()
    if not args.live:
        parser.error('Usá --live para ejecutar la prueba real con tu cuota ChatGPT.')
    try:
        asyncio.run(smoke())
    except (SmokeError, TimeoutError, OSError, ValueError, KeyError) as error:
        # Nunca imprimir errores brutos del servidor: pueden contener datos privados.
        print(f'FALLO: {error}' if isinstance(error, SmokeError)
              else f'FALLO: {type(error).__name__}; prueba incompleta, sin fallback API.')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
