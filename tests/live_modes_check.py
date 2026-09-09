"""Opt-in: tres turnos reales con cuota ChatGPT y ficción efímera; nunca usa Realtime/API."""
import tempfile
from live_mvp import wait
from workbench_ai import Assistant
from workbench_store import Store
from workbench_modes import configure_translation, answer_translation, accept_translation

with tempfile.TemporaryDirectory(prefix='sw-live-modes-') as directory:
    store=Store(directory);project=store.create('Matiz ficticio',workflow='guided',purpose='translation',documents=[dict(name='Original ficticio',content='—Te quiero —dijo Mara al despedirse de Ivo.')],translation=dict(source=0,source_language='es-AR',target_language='en-US'))['id']
    source=store.snapshot(project)['documents'][0]
    configure_translation(store,store.load(project),dict(source=source['id'],source_language='es-AR',target_language='en-US',intent='Conservar la intención del vínculo. No está decidido si es romántico o amistoso: preguntalo antes de traducir.',glossary='Mara e Ivo son nombres propios.'))
    assistant=Assistant(store);assistant.start(project,'translate','Consultá el matiz pendiente antes de traducir.',False)
    run=wait(assistant,store,project);assert run['status']=='completed' and run['translation_result']['question']
    print('OK consulta real de matiz con cita y alternativas:',run['translation_result']['question'],flush=True)
    answer_translation(store,store.load(project),run['id'],'Es afecto amistoso, sin romance. Usar I care about you. Despedida cotidiana, tono sencillo; no hay otros criterios pendientes para este fragmento.')
    assistant.start(project,'translate','Con el criterio registrado, prepará el borrador de esta única frase.',False)
    run=wait(assistant,store,project);assert run['status']=='completed' and run['translation_result']['draft']
    assert len(store.snapshot(project)['documents'])==1
    doc=accept_translation(store,store.load(project),run['id'],run['translation_result']['draft'])
    assert doc['translation_status']=='reviewed' and store.document(store.load(project),source['id'])['content']==source['content']
    print('OK borrador real tras criterio: copia separada únicamente con aprobación explícita del test sobre ficción.',flush=True)
    project=store.create('Mesa ficticia',workflow='guided',purpose='rpg',initial_idea='Un puerto flotante para una mesa de fantasía esperanzadora. Sistema casero todavía por definir.')['id']
    assistant.start_interview(project);run=wait(assistant,store,project)
    assert run['status']=='completed' and run['text'].count('?')==1 and not run['skill']
    assert store.load(project)['documents']==[]
    print('OK entrevista real de rol, sin manuscrito ni reglas impuestas:',run['text'],flush=True)
