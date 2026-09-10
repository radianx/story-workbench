"""Panel y coordinación reales con ficción mínima, sesión ChatGPT y modelos explícitos."""
import sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.workbench_store import Store
from src.workbench_ai import Assistant
from src.workbench_team import team_preferences
with tempfile.TemporaryDirectory(prefix='sw-live-team-') as directory:
    store=Store(directory);project=store.create('Ficción de lectores',True)['id'];assistant=Assistant(store)
    data=store.load(project);data['ai_preferences']={'model':'gpt-5.6-sol','effort':'low'}
    data['team_preferences']=team_preferences(dict(model='gpt-5.6-luna',effort='max',max_agents=2,readers=['impatient','emotional']))
    store.persist(data);before={p:p.read_bytes() for p in store.root.rglob('*.md')}
    for mode,prompt in [('panel','Sintetizá en menos de 150 palabras las lecturas: coincidencias y diferencias. No reescribas.'),('diagnosis','Revisá solamente si el color de la llave contradice el canon. Repartí una tarea de contraste y sintetizá en una frase, sin reescribir.')]:
        assistant.start(project,mode,prompt,False,True)
        deadline=time.monotonic()+650
        while assistant.active and time.monotonic()<deadline:time.sleep(.2)
        if assistant.active:
            assistant.stop(project,assistant.active[1]);raise AssertionError('Tiempo agotado')
        data=store.load(project);run=data['runs'][-1]
        assert run['status']=='completed',(mode,run['status'],run['error'])
        assert (run['model'],run['effort'])==('gpt-5.6-sol','low')
        assert 1<=len(run['team_workers'])<=2
        assert all(w['status']=='completed' and w['model']=='gpt-5.6-luna' and w['effort']=='max' and w['text'] for w in run['team_workers'])
        assert before=={p:p.read_bytes() for p in store.root.rglob('*.md')}
        assert not data['proposals']
        print('OK real:',mode,'; Sol low +',len(run['team_workers']),'Luna max; resultado guardado, sin reescrituras.',flush=True)
