"""Dos turnos reales con selección explícita, solo ficción temporal y sesión ChatGPT."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.workbench_store import Store
from src.workbench_ai import Assistant
from live_mvp import wait

with tempfile.TemporaryDirectory(prefix='sw-model-choice-') as directory:
    store=Store(directory);project=store.create('Selección de modelo',workflow='guided')['id'];assistant=Assistant(store)
    thread=None
    for model,effort,prompt in [
        ('gpt-5.6-luna','medium','Redactá una apertura de 35 palabras. Mara conduce una biblioteca en barco. Tono cálido, tercera persona, asombro. No agregues más personajes.'),
        ('gpt-5.6-sol','high','Escribí una frase de continuación con la misma protagonista. Conservá su nombre y el lugar, sin hacer preguntas.')]:
        data=store.load(project);data['ai_preferences']={'model':model,'effort':effort};store.persist(data)
        assistant.start(project,'draft',prompt,False)
        run=wait(assistant,store,project)
        assert run['status']=='completed',run['error']
        assert (run['model'],run['effort'])==(model,effort)
        assert store.snapshot(project)['documents']==[]
        current=store.load(project)['thread']
        if thread: assert current==thread and 'Mara' in run['text'],run['text']
        thread=current
        print('OK selección real:',model,effort,'; mismo hilo y sin guardado automático.',flush=True)
