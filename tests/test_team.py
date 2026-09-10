import asyncio,json,tempfile,threading,unittest
from unittest.mock import patch
from src.workbench_ai import Assistant
from src.workbench_store import Store,Problem
from src.workbench_team import team_preferences,validate_plan
from test_desktop_features import MODELS


class FakeServer:
    calls=[];instances=[];count=0;hold=False;wrong=False;bad_plan=False
    def __init__(self,*args,**kwargs):
        self.events=[];self.closed=False;self.number=len(self.instances);self.instances.append(self)
    async def __aenter__(self):return self
    async def __aexit__(self,*_):self.closed=True
    async def rpc(self,method,params):
        self.calls.append((self.number,method,params))
        if method=='model/list':return {'data':MODELS,'nextCursor':None}
        if method in ('thread/start','thread/resume'):
            self.model=params['model'];self.thread=params.get('threadId','thread-'+str(self.number))
            return dict(thread={'id':self.thread},modelProvider='openai',model='wrong' if self.wrong and self.number else self.model)
        if method=='turn/start':
            type(self).count+=1;turn='turn-'+str(self.count)
            if 'outputSchema' in params:
                text=json.dumps({'tasks':[dict(title='Revisar escena',assignment='Revisá solo lo pedido.',source_ids=[])]} if not self.bad_plan else {'tasks':[]})
            else:text='Aporte independiente.' if self.number else 'Síntesis para el autor.'
            if not (self.hold and self.number):
                self.events += [{'method':'item/agentMessage/delta','params':dict(threadId=self.thread,turnId=turn,delta=text)},
                                {'method':'turn/completed','params':dict(threadId=self.thread,turn={'id':turn,'status':'completed'})}]
            return {'turn':{'id':turn}}
        raise AssertionError(method)
    async def read(self):
        if self.events:return self.events.pop(0)
        await asyncio.sleep(20)


class TeamTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.project=self.store.create('Ficción ciega',True)['id'];self.assistant=Assistant(self.store)
        data=self.store.load(self.project)
        data['ai_preferences']={'model':'modelo-a','effort':'medium'}
        data['team_preferences']=team_preferences({'model':'modelo-b','effort':'low','max_agents':2})
        data['initial_idea']='SECRETO-DEL-AUTOR'
        data['decisions']=[dict(text='DIAGNOSTICO-PREVIO',status='accepted')]
        data['documents'][0]['synopsis']='SINOPSIS-SECRETA'
        self.store.persist(data)
        FakeServer.calls=[];FakeServer.instances=[];FakeServer.count=0;FakeServer.hold=False;FakeServer.wrong=False;FakeServer.bad_plan=False
    def prepare(self,mode='panel'):
        with patch('threading.Thread.start'):
            self.assistant.start(self.project,mode,'BUSCAR-DEFECTO-SESGADO',False,True)
        data=self.store.load(self.project)
        return data['runs'][-1],[self.store.document(data,d['id']) for d in data['documents'] if d['selected']]
    def execute(self,mode='panel'):
        run,docs=self.prepare(mode)
        with patch('src.workbench_ai.Server',FakeServer),patch('src.workbench_team.Server',FakeServer):
            asyncio.run(self.assistant.execute(self.project,run,docs))
        return self.store.load(self.project)['runs'][-1]
    def test_blind_context_models_and_no_writes(self):
        before={p:p.read_bytes() for p in self.store.root.rglob('*.md')}
        run=self.execute()
        self.assertEqual(run['status'],'completed');self.assertEqual(len(run['team_workers']),2)
        turns=[(i,p) for i,m,p in FakeServer.calls if m=='turn/start']
        self.assertEqual(len(turns),3)
        self.assertEqual([(p['model'],p['effort']) for i,p in turns if i], [('modelo-b','low')]*2)
        for i,p in turns:
            text=json.dumps(p)
            if i:
                for hidden in ('SECRETO-DEL-AUTOR','DIAGNOSTICO-PREVIO','SINOPSIS-SECRETA','BUSCAR-DEFECTO-SESGADO','Aporte independiente.'):
                    self.assertNotIn(hidden,text)
                self.assertIn('llave azul',text)
                self.assertNotIn('Canon del faro',text)
            else:self.assertEqual((p['model'],p['effort']),('modelo-a','medium'))
        self.assertTrue(all(server.closed for server in FakeServer.instances))
        self.assertEqual(before,{p:p.read_bytes() for p in self.store.root.rglob('*.md')})
        self.assertFalse(self.store.load(self.project)['proposals'])
    def test_coordinator_plan_and_model_mismatch(self):
        run=self.execute('diagnosis')
        self.assertEqual(run['status'],'completed');self.assertEqual(len(run['team_workers']),1)
        self.assertEqual(FakeServer.count,3)
        self.assistant.active=None;FakeServer.instances=[];FakeServer.calls=[];FakeServer.wrong=True
        with self.assertRaisesRegex(Problem,'otro modelo'):self.execute('diagnosis')
        self.assertTrue(all(s.closed for s in FakeServer.instances))
        self.assertFalse([p for i,m,p in FakeServer.calls if i and m=='turn/start'])
    def test_validation_before_launch(self):
        for prefs in ({'model':'modelo-b'}, {'model':'modelo-b','effort':'low','max_agents':4}, {'model':'modelo-b','effort':'low','max_agents':True}, {'model':'modelo-b','effort':'low','readers':['impatient','impatient']}):
            with self.assertRaises(Problem):team_preferences(prefs)
        with self.assertRaises(Problem):validate_plan('{"tasks":[{"title":"A","assignment":"B","source_ids":["foreign"]}]}',2,[])
        with self.assertRaises(Problem):self.assistant.start(self.project,'panel','Prueba',False)
        with self.assertRaises(Problem):self.assistant.start(self.project,'interview','Prueba',True,True)
        FakeServer.bad_plan=True
        with self.assertRaises(Problem):self.execute('diagnosis')
        self.assertEqual(len(FakeServer.instances),1)
    def test_cancellation_closes_all_children_and_restart(self):
        run,docs=self.prepare();FakeServer.hold=True
        async def run_and_cancel():
            task=asyncio.create_task(self.assistant.execute(self.project,run,docs))
            for _ in range(100):
                if len([1 for i,m,p in FakeServer.calls if i and m=='turn/start'])==2:break
                await asyncio.sleep(.01)
            self.assistant.cancel.set()
            with self.assertRaises(Problem):await asyncio.wait_for(task,2)
        with patch('src.workbench_ai.Server',FakeServer),patch('src.workbench_team.Server',FakeServer):asyncio.run(run_and_cancel())
        self.assertTrue(all(s.closed for s in FakeServer.instances))
        reopened=Store(self.temp.name);saved=reopened.load(self.project)['runs'][-1]
        self.assertEqual(saved['status'],'interrupted')
        self.assertTrue(all(w['status']=='interrupted' for w in saved['team_workers']))
