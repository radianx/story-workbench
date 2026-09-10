"""Prueba opcional real: usa cuota ChatGPT y solo material ficticio."""
import asyncio
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.codex_smoke import Server
from src.workbench_ai import Assistant, editor_overrides
from src.workbench_store import Store


async def permissions(directory):
    root=Path(directory);agent=root/'agent';agent.mkdir()
    secret=root/'not-selected.txt';secret.write_text('SYNTHETIC-NOT-SELECTED')
    (agent/'escape.txt').symlink_to(secret)
    async with Server(agent,editor_overrides(),experimental=True) as server:
        response=await server.rpc('command/exec',{'command':['python3','-c',
            'import pathlib,errno\n'
            f'paths=[pathlib.Path({str(secret)!r}),pathlib.Path("escape.txt")]\n'
            'for p in paths:\n'
            ' try: p.read_text()\n'
            ' except OSError as e: assert e.errno in (errno.EACCES,errno.EPERM,errno.ENOENT)\n'
            ' else: raise SystemExit(9)\n'
            'try: pathlib.Path("blocked.txt").write_text("x")\n'
            'except OSError as e: assert e.errno in (errno.EACCES,errno.EPERM,errno.EROFS)\n'
            'else: raise SystemExit(10)\n'
            'print("ISOLATED")'], 'cwd':str(agent),'timeoutMs':10000})
        assert response['exitCode']==0 and 'ISOLATED' in response['stdout'], (response['exitCode'],response['stderr'])
    print('OK perfil: lectura fuera del contexto, symlink de escape y escritura bloqueados.',flush=True)


def wait(assistant,store,project):
    deadline=time.monotonic()+270
    while assistant.active and time.monotonic()<deadline: time.sleep(.2)
    assert assistant.active is None,'No terminó la tarea'
    run=store.load(project)['runs'][-1]
    assert run['status'] in ('completed','interrupted'),run['error']
    return run


def interview():
    with tempfile.TemporaryDirectory(prefix='sw-live-interview-') as directory:
        store=Store(directory)
        project=store.create('La biblioteca a la deriva',workflow='guided',
                             initial_idea='Una biblioteca viaja en un barco entre pueblos aislados.')['id']
        assistant=Assistant(store)
        first=assistant.start_interview(project)
        assert assistant.start_interview(project)==first
        run=wait(assistant,store,project)
        assert run['status']=='completed' and run['text'].count('?')==1,run['text']
        print('Primera pregunta real:',run['text'],flush=True)
        data=store.load(project)
        assert data['documents']==[] and len(data['runs'])==1 and data['workflow']=='guided'
        thread=data['thread']
        store=Store(directory);assistant=Assistant(store)
        assert assistant.start_interview(project)==first
        assistant.start(project,'interview',
                        'Quiero que el lector sienta asombro y esperanza. La protagonista es una bibliotecaria llamada Mara.',True)
        run=wait(assistant,store,project)
        assert run['status']=='completed' and run['text'].count('?')==1,run['text']
        assert store.load(project)['thread']==thread and store.load(project)['documents']==[]
        print('Siguiente pregunta real:',run['text'],flush=True)
        print('OK entrevista build-novel: proyecto vacío, una pregunta por turno, respuestas persistidas, sin duplicación ni manuscrito automático.',flush=True)


def main():
    with tempfile.TemporaryDirectory(prefix='sw-permissions-') as d:asyncio.run(permissions(d))
    with tempfile.TemporaryDirectory(prefix='sw-live-mvp-') as d:
        store=Store(d);project=store.create('Prueba editorial ficticia',True)['id'];assistant=Assistant(store)
        original=store.snapshot(project)['documents'][0]['content']
        assistant.start(project,'diagnosis','Recordá la clave ficticia BRUMA-572. Señalá solo la contradicción del color de la llave.')
        run=wait(assistant,store,project);assert run['status']=='completed' and 'roja' in run['text'].lower()
        first_thread=store.load(project)['thread']
        assert store.snapshot(project)['documents'][0]['content']==original
        print('OK diagnóstico real sin modificar documentos.',flush=True)
        # Reiniciar el gestor de la aplicación y reanudar el hilo persistido.
        store=Store(d);assistant=Assistant(store)
        assistant.start(project,'chat','¿Qué clave ficticia te pedí recordar? Respondé solo la clave.')
        run=wait(assistant,store,project);assert 'BRUMA-572' in run['text'] and store.load(project)['thread']==first_thread
        print('OK conversación recuperada tras reinicio del gestor.',flush=True)
        assistant.start(project,'proposal','Proponé exactamente un bloque para cambiar "llave azul" por "llave roja" en La última luz. No cambies nada más.')
        wait(assistant,store,project)
        data=store.snapshot(project);assert data['documents'][0]['content']==original and len(data['proposals'])>=1
        proposal=data['proposals'][0];assert proposal['status']=='pending'
        with store.lock:data=store.decide(project,proposal['id'],True)
        assert 'llave roja' in data['documents'][0]['content']
        print('OK propuesta estructurada real y aceptación explícita de un bloque.',flush=True)
        assistant.start(project,'chat','Enumerá 200 posibles nombres ficticios de faros, uno por línea.')
        deadline=time.monotonic()+90
        while assistant.active and time.monotonic()<deadline:
            run=store.load(project)['runs'][-1]
            if run['text']:
                with store.lock:assistant.stop(project,run['id'])
                break
            time.sleep(.2)
        run=wait(assistant,store,project);assert run['status']=='interrupted'
        print('OK cancelación real desde el gestor del MVP.',flush=True)
        with store.lock:
            data=store.load(project);data['documents'][-1]['selected']=False;store.persist(data)
        assistant.start(project,'chat','Decí listo en una palabra.')
        wait(assistant,store,project)
        assert store.load(project)['thread']!=first_thread
        print('OK retirar una fuente abre hilo nuevo.',flush=True)


if __name__=='__main__':
    if '--interview-only' in sys.argv:interview()
    else:main();interview()
