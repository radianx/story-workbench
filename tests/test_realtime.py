"""Contrato Realtime con transporte simulado: no usa clave real ni genera cargos."""
import io
import json
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
from workbench_store import Store, Problem
from workbench_realtime import Realtime, NoRedirects, context
import test_workbench

KEY='sk-ficticia-solo-test-no-es-una-credencial'
class RealtimeTests(unittest.TestCase):
    def test_reading_tokens_have_no_tools_or_project_context(self):
        engine=Realtime();engine.configure(KEY);engine.configure('AQ.ficticia-solo-test','gemini')
        with patch('workbench_realtime.urllib.request.build_opener') as opener:
            for provider,consent in [('openai',False),('gemini',False),('other',True)]:
                with self.assertRaises(Problem):engine.read_session(provider,consent)
            opener.assert_not_called()
            for provider,body in [('openai',b'{"value":"ephemeral-fixture"}'),('gemini',b'{"name":"ephemeral-fixture"}')]:
                opener.return_value.open.return_value=io.BytesIO(body)
                result=engine.read_session(provider,True)
                self.assertEqual(result['token'],'ephemeral-fixture')
                request=opener.return_value.open.call_args.args[0];payload=json.loads(request.data)
                setup=payload.get('session') or payload['bidiGenerateContentSetup']
                self.assertFalse(setup.get('tools'));self.assertNotIn('get_context',json.dumps(payload));self.assertNotIn(KEY,json.dumps(result))
                if provider=='openai':
                    self.assertEqual(payload['expires_after']['seconds'],60)
                    self.assertIsNone(setup['audio']['input']['turn_detection'])
                opener.return_value.open.side_effect=urllib.error.HTTPError(request.full_url,401,KEY,{},None)
                with self.assertRaises(Problem) as error:engine.read_session(provider,True)
                self.assertNotIn(KEY,str(error.exception));self.assertFalse(engine.connecting.locked())
                opener.return_value.open.side_effect=None
    def test_opt_in_transport_context_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);project=store.create('Voz ficticia',True)['id']
            hidden=store.add_document(project,'Referencia sin seleccionar','referencia','NO-ENVIAR',selected=False)
            data=store.snapshot(project);engine=Realtime()
            with patch('workbench_realtime.urllib.request.build_opener') as opener:
                for consent,actions in [(False,True),(True,'yes'),(True,True)]:
                    with self.assertRaises(Problem):engine.connect(data,'v=0\r\n',consent,actions)
                opener.assert_not_called()
                engine.configure(KEY)
                with self.assertRaises(Problem):engine.connect(data,'v=0\r\n',False,True)
                opener.assert_not_called()
                opener.return_value.open.return_value=io.BytesIO(b'v=0\r\nanswer')
                self.assertEqual(engine.connect(data,'v=0\r\noffer',True,True)['model'],'gpt-realtime')
                request=opener.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url,'https://api.openai.com/v1/realtime/calls')
                body=request.data.decode();self.assertIn('"model": "gpt-realtime"',body);self.assertIn('workbench_action',body)
                self.assertNotIn('NO-ENVIAR',body);self.assertNotIn(KEY,body)
                self.assertEqual(request.get_header('Authorization'),'Bearer '+KEY)
                opener.return_value.open.return_value=io.BytesIO(b'v=0\r\nanswer')
                engine.connect(data,'v=0',True,False)
                self.assertNotIn('workbench_action',opener.return_value.open.call_args.args[0].data.decode())
                opener.return_value.open.side_effect=urllib.error.HTTPError(request.full_url,401,KEY,{},None)
                with self.assertRaises(Problem) as error:engine.connect(data,'v=0',True,True)
                self.assertNotIn(KEY,str(error.exception));self.assertIn('rechazada',str(error.exception))
                self.assertFalse(engine.connecting.locked())
            self.assertNotIn(KEY,json.dumps(engine.status()))
            self.assertNotIn(KEY,json.dumps(store.snapshot(project)))
            self.assertTrue(any(d['id']==hidden['id'] for d in context(data)['library']))
            data['runs']=[dict(purpose='novel',text='NO-ENVIAR-HISTORIAL',sources=[dict(id=hidden['id'],hash=hidden['hash'])])]
            self.assertNotIn('NO-ENVIAR-HISTORIAL',json.dumps(context(data)))
            data['initial_idea']='x'*60001
            with self.assertRaises(Problem):context(data)
            with self.assertRaises(Problem):NoRedirects().redirect_request(None,None,None,None,None,None)
            engine.configure('');self.assertFalse(engine.status()['configured'])
            for key in ('not-a-key','sk-with whitespace',None):
                with self.assertRaises(Problem):engine.configure(key)

class RealtimeHTTP(unittest.TestCase):
    setUp=test_workbench.HTTPTests.setUp
    request=test_workbench.HTTPTests.request
    def test_authenticated_memory_key_and_consent(self):
        self.assertEqual(self.request('/api/realtime')[0],200)
        self.assertFalse(json.loads(self.request('/api/voice-storage')[1])['available'])
        self.assertEqual(self.request('/api/voice-storage',headers={'Authorization':'bad'})[0],401)
        self.assertEqual(self.request('/api/realtime/key',{'key':KEY},headers={'Authorization':'bad'})[0],401)
        code,body=self.request('/api/realtime/key',{'key':KEY});self.assertEqual(code,200);self.assertNotIn(KEY.encode(),body)
        project=self.server.store.create('Prueba local')['id']
        self.assertEqual(self.request('/api/projects/'+project+'/voice-context')[0],200)
        with patch('workbench_realtime.urllib.request.build_opener') as opener:
            self.assertEqual(self.request('/api/realtime/connect',dict(project=project,sdp='v=0',consent=False,actions=True))[0],400)
            opener.assert_not_called()
            self.assertEqual(self.request('/api/realtime/read-session',dict(provider='openai',consent=True),headers={'Authorization':'bad'})[0],401)
            self.assertEqual(self.request('/api/realtime/read-session',dict(provider='openai',consent=False))[0],400)
            opener.assert_not_called()
        self.assertEqual(self.request('/api/realtime/key',{'key':''})[0],200)

class GeminiTests(unittest.TestCase):
    def test_single_use_scoped_token_without_openai_key(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);project=store.create('Gemini ficticio',True)['id'];engine=Realtime()
            for key in ['AQ.ficticia-solo-test','AIza-ficticia-solo-test']:
                engine.configure(key,'gemini')
                self.assertTrue(engine.status()['providers']['gemini'])
            for key in ['AQ.con espacio ficticio','AQ.con\nficticio','sk-ficticia-solo-test']:
                with self.assertRaises(Problem):engine.configure(key,'gemini')
            self.assertFalse(engine.status()['configured']);self.assertTrue(engine.status()['providers']['gemini'])
            with patch('workbench_realtime.urllib.request.build_opener') as opener:
                with self.assertRaises(Problem):engine.connect_gemini(store.snapshot(project),False,True)
                opener.assert_not_called()
                opener.return_value.open.return_value=io.BytesIO(b'{"name":"auth_tokens/temporal-ficticio"}')
                result=engine.connect_gemini(store.snapshot(project),True,True)
                request=opener.return_value.open.call_args.args[0];body=json.loads(request.data)
                self.assertEqual(request.full_url,'https://generativelanguage.googleapis.com/v1beta/auth_tokens')
                self.assertNotIn('AIza',result['token']);self.assertNotIn('AIza',json.dumps(result))
                self.assertEqual(body['uses'],1);self.assertEqual(body['bidiGenerateContentSetup'],result['setup'])
                self.assertEqual(result['model'],'gemini-3.1-flash-live-preview')
                self.assertIn('workbench_action',json.dumps(result['setup']['tools']))
                opener.return_value.open.return_value=io.BytesIO(b'{"name":"temporary"}')
                result=engine.connect_gemini(store.snapshot(project),True,False)
                self.assertNotIn('workbench_action',json.dumps(result['setup']['tools']))
                opener.return_value.open.side_effect=urllib.error.HTTPError(request.full_url,403,'AIza-secret',{},None)
                with self.assertRaises(Problem) as error:engine.connect_gemini(store.snapshot(project),True,True)
                self.assertNotIn('AIza',str(error.exception));self.assertFalse(engine.connecting.locked())
            with self.assertRaises(Problem):engine.configure(KEY,'gemini')
            with self.assertRaises(Problem):engine.configure(KEY,'unknown')
            engine.configure('','gemini');self.assertFalse(engine.status()['providers']['gemini'])
