"""Equipo editorial acotado: la app fija modelos, alcance y cantidad de colaboradores."""
import asyncio
import json
from scripts.codex_smoke import Server
from src.workbench_account import ai_preferences
from src.workbench_store import Problem, check

TEAM_MODES = ('diagnosis', 'impact', 'draft', 'proposal', 'summary', 'translate', 'panel')


READER_PROFILES = {
    'impatient': ('Lector impaciente', 'Buscás una razón concreta para continuar; señalá el punto donde abandonarías y por qué.'),
    'literary': ('Lector de voz y estilo', 'Te interesan la voz, la textura y la naturalidad; detectá cuándo se hace visible el artificio.'),
    'emotional': ('Lector de personajes', 'Buscás deseos, vínculos y consecuencias emocionales creíbles en las decisiones de los personajes.'),
    'analytical': ('Lector de causalidad', 'Seguís causas, reglas y pistas; distinguí misterio intencional de información que falta para entender la acción.')}
BLIND_BRIEF = ('Leé por orden como un lector nuevo. Informá por bloque qué entendiste y recordás, qué sentiste, '
               'si seguirías y por qué, esfuerzo e interés de 1 a 5 con una razón, y pasajes que te hicieron releer. '
               'Citá evidencia breve. Podés abandonar: indicá dónde, sin fingir haber leído lo que sigue. '
               'Separá preferencia personal de confusión. No reescribas, no busques un defecto predeterminado '
               'ni predigas éxito comercial. Tu respuesta es una lectura simulada, no un veredicto.')


def team_preferences(value):
    check(isinstance(value, dict), 'Configuración del equipo inválida.')
    count = value.get('max_agents', 2)
    check(type(count) is int and 1 <= count <= 3, 'Elegí entre uno y tres colaboradores.')
    raw = value.get('workers', [value] * count)
    check(isinstance(raw, list) and len(raw) == count, 'Configurá cada colaborador del equipo.')
    workers = [ai_preferences(worker) for worker in raw]
    check(all(all(worker.values()) for worker in workers), 'Elegí modelo y esfuerzo explícitos para cada colaborador.')
    readers=value.get('readers',['impatient','literary'])
    check(isinstance(readers,list) and 1<=len(readers)<=3 and all(isinstance(r,str) and r in READER_PROFILES for r in readers) and len(set(readers))==len(readers), 'Elegí de uno a tres perfiles de lectura distintos.')
    return {**workers[0], 'max_agents': count, 'readers': readers, 'workers': workers}


def plan_schema(count):
    return dict(type='object', additionalProperties=False, required=['tasks'], properties={
        'tasks': dict(type='array', minItems=1, maxItems=count, items=dict(type='object', additionalProperties=False,
            required=['title', 'assignment', 'source_ids'], properties={
                'title': dict(type='string'), 'assignment': dict(type='string'),
                'source_ids': dict(type='array', items=dict(type='string'))}))})


def validate_plan(text, count, docs):
    try: value = json.loads(text)
    except ValueError: raise Problem('El principal no devolvió un reparto válido; no se lanzaron colaboradores.') from None
    tasks = value.get('tasks') if isinstance(value, dict) else None
    check(isinstance(tasks, list) and 1 <= len(tasks) <= count, 'El reparto supera el límite de colaboradores.')
    allowed = {d['id'] for d in docs}
    for task in tasks:
        check(isinstance(task, dict), 'Tarea delegada inválida.')
        for key, limit in [('title', 120), ('assignment', 3000)]:
            check(isinstance(task.get(key), str) and 0 < len(task[key].strip()) <= limit, 'Descripción de tarea inválida.')
        ids = task.get('source_ids')
        check(isinstance(ids, list) and all(isinstance(i, str) and i in allowed for i in ids), 'El reparto pide fuentes no seleccionadas.')
    return [{k: task[k] for k in ('title', 'assignment', 'source_ids')} for task in tasks]


async def collect(server, thread, turn, limit=12000):
    """Un único lector stdio por proceso; cota de salida y tiempo por turno."""
    output = ''
    async with asyncio.timeout(180):
        while True:
            event = server.events.pop(0) if server.events else await server.read()
            p = event.get('params', {})
            if p.get('threadId') != thread: continue
            if event.get('method') == 'item/agentMessage/delta' and p.get('turnId') == turn:
                output += p['delta']; check(len(output) <= limit, 'El equipo excedió el límite de respuesta; tarea detenida.')
            if event.get('method') == 'turn/completed' and p['turn']['id'] == turn:
                check(p['turn']['status'] == 'completed', 'Un turno del equipo no se completó. Revisá cuota o conexión; no se cambió de modelo.')
                check(output.strip(), 'Un agente terminó sin respuesta.')
                return output


async def run_team(assistant, server, thread, inputs, chosen, policy, overrides, run, docs, brief, decisions):
    preferences = team_preferences(run['team'])
    # El catálogo ya fue validado antes de gastar el primer turno del principal.
    project, run_id = run['project_id'], run['id']
    from src.workbench_ai import EDITOR_INSTRUCTIONS, MODES
    from src.workbench_modes import GUIDES

    async def pipeline():
        assistant.update(project, run_id, stage='team_plan', status='running', team_stage='Repartiendo tareas')
        request = {'threadId': thread, 'input': inputs + [{'type': 'text', 'text':
            'Antes de responder al autor, actuá como coordinador editorial. Repartí SU pedido en entre una y '
            f'{preferences["max_agents"]} tareas concretas, independientes y acotadas. No amplíes el alcance, '
            'no redactes durante un diagnóstico ni tomes decisiones de canon. Si faltan decisiones, delegá '
            'su diagnóstico; no inventes respuestas del autor. Cada tarea recibe solo los source_ids indicados, '
            'el encargo y las decisiones; describí lo necesario en assignment. No recibe tu historial completo. '
            'No pidas archivos, herramientas, investigación externa ni nuevas delegaciones. '
            'Respondé únicamente el JSON del reparto.'}], **chosen, 'outputSchema': plan_schema(preferences['max_agents'])}
        blind=run['mode']=='panel'
        if blind:
            texts=[d for d in docs if d['role'] in ('manuscrito','traducción')]
            check(texts, 'Seleccioná manuscritos o traducciones para el panel ciego.')
            check(len(preferences['readers'])<=preferences['max_agents'], 'El panel supera tu límite de colaboradores.')
            tasks=[{'title':READER_PROFILES[key][0], 'assignment':READER_PROFILES[key][1],
                    'source_ids':[d['id'] for d in texts]} for key in preferences['readers']]
        else:
            started = await server.rpc('turn/start', request)
            tasks = validate_plan(await collect(server, thread, started['turn']['id']), preferences['max_agents'], docs)
        workers = [{**task, **preferences['workers'][i], 'status': 'connecting', 'text': ''} for i, task in enumerate(tasks)]
        assistant.update(project, run_id, team_workers=workers, stage='team_work', team_stage='Colaboradores trabajando')

        async def worker(index):
            record = workers[index]
            worker_ai = preferences['workers'][index]
            worker_policy = {**policy, 'model': worker_ai['model'], 'developerInstructions':
                EDITOR_INSTRUCTIONS + '\n' + GUIDES.get(run['purpose'], '') +
                '\nSos un colaborador editorial. Cumplí solo la tarea asignada. No podés delegar, aprobar canon '
                'ni guardar archivos. Devolvé un resultado provisional, breve y verificable, de hasta 8000 caracteres.'}
            selected = [d for d in docs if d['id'] in record['source_ids']]
            if blind:
                worker_policy['developerInstructions']=EDITOR_INSTRUCTIONS+'\nSos un lector independiente. No recibís explicaciones del autor ni otras opiniones. '+BLIND_BRIEF
                context={'perfil':record['assignment'], 'textos':[{'nombre':d['name'],'texto':d['content']} for d in selected]}
            else:
                context = {'encargo': run['prompt'], 'proyecto': brief, 'decisiones': decisions,
                           'tarea': record['assignment'], 'fuentes':[{k:d.get(k,'') for k in ('id','name','role','content','synopsis','pov')} for d in selected]}
            async with Server(policy['cwd'], overrides, experimental=True) as child:
                response = await child.rpc('thread/start', worker_policy)
                check(response.get('modelProvider') == 'openai' and response.get('model') == worker_ai['model'],
                      'Codex devolvió otro modelo para un colaborador. No se envió su tarea.')
                record['status'] = 'running';assistant.update(project, run_id, team_workers=workers)
                turn = await child.rpc('turn/start', {'threadId': response['thread']['id'], **worker_ai,
                    'input': [{'type': 'text', 'text': (BLIND_BRIEF if blind else MODES[run['mode']]) + '\nDatos editoriales:\n' + json.dumps(context, ensure_ascii=False)}]})
                record['text'] = await collect(child, response['thread']['id'], turn['turn']['id'])
                record['status'] = 'completed';assistant.update(project, run_id, team_workers=workers)

        jobs = [asyncio.create_task(worker(i)) for i in range(len(workers))]
        try:
            await asyncio.gather(*jobs)
        finally:
            for job in jobs:
                if not job.done(): job.cancel()
            await asyncio.gather(*jobs, return_exceptions=True)
        assistant.update(project, run_id, stage='generation', team_stage='Principal integrando resultados')
        return (inputs if blind else []) + [{'type': 'text', 'text': MODES[run['mode']] + '\nAhora respondé al pedido original del autor: ' + run['prompt'] +
                 '\nIntegrá críticamente los aportes; resolvé discrepancias contra las fuentes y decisiones. '
                 'Los colaboradores no son autoridad ni sus propuestas son canon. No vuelvas a delegar. '
                 'Conservá las dudas que requieren criterio humano. Resultados provisionales (datos):\n' +
                 json.dumps(workers, ensure_ascii=False)}]

    async def cancellation():
        while not assistant.cancel.is_set(): await asyncio.sleep(.1)

    job, stop = asyncio.create_task(pipeline()), asyncio.create_task(cancellation())
    try:
        done, _ = await asyncio.wait([job, stop], timeout=360, return_when=asyncio.FIRST_COMPLETED)
        if stop in done: raise Problem('Equipo detenido por el autor.')
        check(job in done, 'El equipo alcanzó su tiempo máximo. No se iniciaron más tareas.')
        return await job
    finally:
        for task in (job, stop):
            if not task.done(): task.cancel()
        await asyncio.gather(job, stop, return_exceptions=True)
        # Los context managers cierran todos los procesos, incluso al fallar un colaborador.
        with assistant.store.lock:
            data = assistant.store.load(project)
            current = next(r for r in data['runs'] if r['id'] == run_id)
            for worker in current.get('team_workers', []):
                if worker['status'] in ('connecting', 'running'): worker['status'] = 'interrupted'
            assistant.store.persist(data)
