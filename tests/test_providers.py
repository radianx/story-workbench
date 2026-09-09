"""Protocolos experimentales con SSE ficticio, sin credenciales ni llamadas reales."""
import io,json,tempfile,threading,unittest,urllib.error
from unittest.mock import patch
from workbench_providers import Providers,engine_preferences
from workbench_store import Store,Problem
from workbench_ai import Assistant,portable_history

class Response(io.BytesIO):
    headers={'Content-Type':'text/event-stream'}

def events(*values):
    return Response(b''.join(b'data: '+(v.encode() if isinstance(v,str) else json.dumps(v).encode())+b'\n\n' for v in values))

class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.providers=Providers()
        for provider in self.providers.status():self.providers.configure(provider,'ficticia-clave-de-prueba')

    def test_requests_and_streams(self):
        samples={
            'openai':[{'type':'response.output_text.delta','delta':'Hola'}, {'type':'response.completed','response':{'status':'completed','model':'real-version'}}],
            'gemini':[{'candidates':[{'content':{'parts':[{'text':'razonamiento','thought':True},{'text':'Hola'}]},'finishReason':'STOP'}],'modelVersion':'real-version'}],
            'anthropic':[{'type':'message_start','message':{'model':'real-version'}},{'type':'content_block_delta','delta':{'type':'text_delta','text':'Hola'}},{'type':'message_delta','delta':{'stop_reason':'end_turn'}},{'type':'message_stop'}]}
        for p in ('deepseek','kimi','local'):samples[p]=[{'model':'real-version','choices':[{'delta':{'content':'Hola'},'finish_reason':'stop'}]},'[DONE]']
        for provider,stream in samples.items():
            with self.subTest(provider=provider):
                engine={'provider':provider,'model':'test-model'}
                request=self.providers.request(engine,'reglas','fuentes')
                body=json.loads(request.data)
                self.assertNotIn('ficticia-clave',request.full_url)
                self.assertIn('fuentes',request.data.decode())
                self.assertNotIn('tools',body)
                if provider=='openai':self.assertFalse(body['store']);self.assertEqual(body['max_output_tokens'],8192)
                if provider=='gemini':self.assertEqual(request.get_header('X-goog-api-key'),'ficticia-clave-de-prueba');self.assertNotIn('model',body)
                if provider=='anthropic':self.assertEqual(request.get_header('Anthropic-version'),'2023-06-01');self.assertEqual(body['max_tokens'],8192)
                if provider=='local':self.assertTrue(request.full_url.startswith('http://127.0.0.1:11434/v1/'))
                with patch('urllib.request.OpenerDirector.open',return_value=events(*stream)):
                    output=list(self.providers.stream(engine,'reglas','fuentes',threading.Event()))
                self.assertEqual(''.join(t for t,m in output),'Hola');self.assertIn('real-version',[m for t,m in output])

    def test_invalid_streams_no_success_or_secret_errors(self):
        for stream in ([{'choices':[{'delta':{'content':'truncado'},'finish_reason':'length'}]}],['[DONE]'],[{'error':{'message':'ficticia-clave-de-prueba'}}],[{'choices':[{'delta':{'content':'cortado'}}]}]):
            with patch('urllib.request.OpenerDirector.open',return_value=events(*stream)):
                with self.assertRaises(Problem) as caught:list(self.providers.stream({'provider':'kimi','model':'test'},'','',threading.Event()))
                self.assertNotIn('ficticia-clave',str(caught.exception))
        with patch('urllib.request.OpenerDirector.open',side_effect=urllib.error.HTTPError('private',401,'secret',{},None)):
            with self.assertRaisesRegex(Problem,'HTTP 401'):list(self.providers.stream({'provider':'kimi','model':'test'},'','',threading.Event()))
        cancel=threading.Event();cancel.set()
        with patch('urllib.request.OpenerDirector.open',return_value=events('[DONE]')):
            self.assertEqual(list(self.providers.stream({'provider':'kimi','model':'test'},'','',cancel)),[])

    def test_boundaries(self):
        for endpoint in ('https://evil.test/v1','http://127.0.0.1.evil.test:80/v1','http://user:secret@127.0.0.1:80/v1','http://127.0.0.1:80/v1?key=secret','http://127.0.0.1:80/api','http://127.0.0.1:99999/v1'):
            with self.assertRaises(Problem):engine_preferences({'provider':'local','model':'x','endpoint':endpoint})
        self.assertEqual(engine_preferences({'provider':'local','model':'qwen:8b','endpoint':'http://localhost:1234/v1/'})['endpoint'],'http://127.0.0.1:1234/v1')
        for value in ({'provider':'bad'},{'provider':'gemini','model':'models/x'}, {'provider':'kimi','model':'x\nheader'}):
            with self.assertRaises(Problem):engine_preferences(value)
        for key in ('short','fake\r\nheader',True):
            with self.assertRaises(Problem):self.providers.configure('kimi',key)
        self.providers.configure('openai','')
        with self.assertRaises(Problem):self.providers.request({'provider':'openai','model':'test'},'','')
        self.assertEqual(engine_preferences({}),{'provider':'codex'})

    def test_editorial_flow_history_and_approvals(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);project=store.create('Ficción',True)['id'];assistant=Assistant(store)
            assistant.providers=self.providers
            data=store.load(project);data['engine']={'provider':'kimi','model':'test'};store.persist(data)
            def run(mode,output):
                with patch.object(self.providers,'stream',return_value=iter([(output,'test')])):
                    result=assistant.start(project,mode,'Petición ficticia');assistant.thread.join(5)
                self.assertFalse(assistant.thread.is_alive())
                return store.load(project)['runs'][-1]
            first=run('chat','Respuesta ficticia');self.assertEqual(first['status'],'completed');self.assertEqual(first['provider'],'kimi')
            data=store.snapshot(project);docs=[d for d in data['documents'] if d['selected']]
            next_run={**first,'id':'next'};self.assertIn('Respuesta ficticia',portable_history(data,next_run,docs))
            data['history_start']=len(data['runs']);self.assertNotIn('Respuesta ficticia',portable_history(data,next_run,docs))
            doc=docs[0];before=doc['content'];proposal={'summary':'Sugerencia','proposals':[{'document_id':doc['id'],'before':before,'after':before+'\nCambio','reason':'Prueba'}]}
            result=run('proposal',json.dumps(proposal));self.assertEqual(result['status'],'completed')
            snapshot=store.snapshot(project);self.assertEqual(snapshot['documents'][0]['content'],before);self.assertEqual(snapshot['proposals'][0]['status'],'pending')
            self.assertEqual(run('proposal','Texto no JSON')['status'],'failed');self.assertEqual(len(store.load(project)['proposals']),1)
            self.assertNotIn('ficticia-clave-de-prueba',json.dumps(store.load(project)))

if __name__=='__main__':unittest.main()
