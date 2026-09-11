import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from src.app import AppServer
from src.workbench_ai import Assistant
from src.workbench_store import Store, Problem, digest


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.project = self.store.create('Ficción de prueba', True)['id']

    def test_archive_restores_library_without_deleting_content(self):
        data=self.store.load(self.project)
        before={p.relative_to(self.store.root):p.read_bytes() for p in self.store.root.rglob('*') if p.is_file() and p.name!='project.json'}
        self.store.archive_project(data,True)
        self.assertEqual(self.store.list_projects(),[])
        self.assertEqual(self.store.list_projects(archived=True)[0]['id'],self.project)
        self.assertEqual(self.store.snapshot(self.project)['documents'][0]['content'],self.store.document(data,data['documents'][0]['id'])['content'])
        with self.assertRaises(Problem):Assistant(self.store).start(self.project,'chat','No iniciar oculto')
        with self.assertRaises(Problem):self.store.archive_project(data,'true')
        reopened=Store(self.temp.name)
        self.assertEqual(reopened.list_projects(),[])
        reopened.archive_project(reopened.load(self.project),False)
        self.assertEqual(reopened.list_projects()[0]['id'],self.project)
        self.assertEqual(before,{p.relative_to(self.store.root):p.read_bytes() for p in self.store.root.rglob('*') if p.is_file() and p.name!='project.json'})
        restored=reopened.load(self.project)
        self.assertEqual({k:v for k,v in restored.items() if k not in ('archived','updated')},{k:v for k,v in data.items() if k not in ('archived','updated')})
        restored['runs']=[dict(id='interrupted',status='running')]
        with self.assertRaises(Problem):reopened.archive_project(restored,True)
        restored['archived']=True;reopened.persist(restored)
        recovered=Store(self.temp.name)
        self.assertEqual(recovered.load(self.project)['runs'][0]['status'],'interrupted')
        self.assertEqual(recovered.list_projects(),[])

    def test_workflows_and_legacy_projects(self):
        guided=self.store.create('Idea nueva',workflow='guided',initial_idea='Una biblioteca en el mar.')
        self.assertEqual(guided['documents'],[])
        self.assertEqual(guided['workflow'],'guided')
        self.assertEqual(self.store.load(guided['id'])['initial_idea'],'Una biblioteca en el mar.')
        writing=self.store.create('Página en blanco')
        self.assertEqual(len(writing['documents']),1)
        self.assertEqual(self.store.document(writing,writing['documents'][0]['id'])['content'],'')
        writing.pop('schema_version');del writing['workflow'];del writing['initial_idea'];self.store.persist(writing)
        self.assertEqual(self.store.load(writing['id'])['workflow'],'writing')
        with self.assertRaises(Problem):
            self.store.create('No crear',workflow='invalid')

    def test_interview_without_sources_and_idempotent_start(self):
        project=self.store.create('Entrevista',workflow='guided')['id']
        assistant=Assistant(self.store)
        with self.assertRaises(Problem):
            assistant.start(project,'diagnosis','Sin fuentes')
        with self.assertRaises(Problem):
            assistant.start(project,'interview','Sin skill',False)
        with patch('src.workbench_ai.threading.Thread.start') as start:
            first=assistant.start_interview(project)
            self.assertEqual(assistant.start_interview(project),first)
            self.assertEqual(assistant.start_interview(project,True),first)
            self.assertEqual(start.call_count,1)
            run=self.store.load(project)['runs'][0]
            self.assertTrue(run['skill']);self.assertEqual(run['sources'],[])
            assistant.update(project,first['id'],status='failed',error='Fallo simulado')
            assistant.active=None
            self.assertEqual(assistant.start_interview(project),first)
            retry=assistant.start_interview(project,True)
            self.assertNotEqual(retry,first);self.assertEqual(start.call_count,2)
        with self.assertRaises(Problem):
            assistant.start_interview(self.project)

    def test_conflict_history_and_restore(self):
        data = self.store.load(self.project)
        doc = self.store.document(data, data['documents'][0]['id'])
        saved = self.store.save_document(data, doc['id'], 'Cambio aprobado', doc['hash'])
        with self.assertRaises(Problem) as error:
            self.store.save_document(data, doc['id'], 'No debe pisar', doc['hash'])
        self.assertEqual(error.exception.status, 409)
        version = saved['history'][0]
        old = self.store.path(self.project, 'history', version['id']+'.md').read_text()
        restored = self.store.save_document(data, doc['id'], old, saved['hash'], 'Restaurar')
        self.assertEqual(restored['content'], doc['content'])
        self.assertEqual(len(restored['history']), 2)
        self.assertEqual(Store(self.temp.name).document(data, doc['id'])['content'], doc['content'])

    def test_external_edit_and_symlinks(self):
        data = self.store.load(self.project)
        doc = self.store.document(data, data['documents'][0]['id'])
        path = self.store.path(self.project, 'documents', doc['id']+'.md')
        path.write_text('Otro editor')
        with self.assertRaises(Problem):
            self.store.save_document(data, doc['id'], 'Pérdida', doc['hash'])
        path.unlink()
        path.symlink_to(Path(self.temp.name)/'outside.md')
        with self.assertRaises(Problem):
            self.store.document(data, doc['id'])
        for project in ('../../tmp', '', None, 'abc', '/etc/passwd'):
            with self.assertRaises(Problem):
                self.store.load(project)

    def test_proposals_accept_reject_and_project_isolation(self):
        doc = self.store.add_document(self.project, 'Pasajes', 'manuscrito', 'La llave azul. La puerta blanca.')
        data = self.store.load(self.project)
        run = {'id':'run', 'source_texts':{doc['id']:doc['content']}}
        proposals = [dict(document_id=doc['id'], before='azul', after='roja', reason='Canon de color'),
                     dict(document_id=doc['id'], before='blanca', after='verde', reason='Otra propuesta')]
        self.store.proposals_from_result(data, run, proposals)
        self.store.persist(data)
        first, second = data['proposals']
        result = self.store.decide(self.project, first['id'], True)
        self.assertEqual(result['documents'][-1]['content'], 'La llave roja. La puerta blanca.')
        result = self.store.decide(self.project, second['id'], False)
        self.assertEqual(result['documents'][-1]['content'], 'La llave roja. La puerta blanca.')
        self.assertEqual([d['status'] for d in result['decisions']], ['accepted','rejected'])
        with self.assertRaises(Problem):
            self.store.decide(self.project, first['id'], True)
        other = self.store.create('Otro universo')
        with self.assertRaises(Problem):
            self.store.document(other, doc['id'])
        self.assertEqual(other['runs'], [])
        with self.assertRaises(Problem):
            self.store.proposals_from_result(other, {'id':'x','source_texts':{}}, proposals)

    def test_accept_disjoint_blocks_separately(self):
        doc=self.store.add_document(self.project,'Bloques','manuscrito','Llave azul. Puerta blanca.')
        data=self.store.load(self.project)
        self.store.proposals_from_result(data,{'id':'run','source_texts':{doc['id']:doc['content']}},[
            dict(document_id=doc['id'],before='azul',after='roja',reason='Color de llave'),
            dict(document_id=doc['id'],before='blanca',after='verde',reason='Color de puerta')])
        self.store.persist(data)
        first,second=data['proposals']
        self.store.decide(self.project,first['id'],True)
        result=self.store.decide(self.project,second['id'],True)
        self.assertEqual(result['documents'][-1]['content'],'Llave roja. Puerta verde.')

    def test_proposal_invalid_result_is_atomic_and_stale_rejected(self):
        data = self.store.load(self.project)
        doc = self.store.document(data, data['documents'][0]['id'])
        run = {'id':'run','source_texts':{doc['id']:doc['content']}}
        valid = dict(document_id=doc['id'],before='llave azul',after='llave roja',reason='Canon')
        with self.assertRaises(Problem):
            self.store.proposals_from_result(data,run,[valid,{**valid,'before':'no existe'}])
        self.assertEqual(data['proposals'],[])
        self.store.proposals_from_result(data,run,[valid]);self.store.persist(data)
        self.store.save_document(data,doc['id'],doc['content']+' Cambio externo.',doc['hash'])
        with self.assertRaises(Problem) as error:
            self.store.decide(self.project,data['proposals'][0]['id'],True)
        self.assertEqual(error.exception.status,409)

    def test_restart_and_context_budget(self):
        data=self.store.load(self.project)
        data['runs']=[dict(id='run',status='running',source_texts={})]
        self.store.persist(data)
        restarted=Store(self.temp.name)
        self.assertEqual(restarted.load(self.project)['runs'][0]['status'],'interrupted')
        self.store.add_document(self.project,'Grande','referencia','x'*60001)
        assistant=Assistant(self.store)
        with patch('src.workbench_ai.threading.Thread.start'):
            assistant.start(self.project,'chat','Pregunta')
        self.assertIn('x'*60001, self.store.load(self.project)['runs'][-1]['source_texts'].values())


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.server=AppServer(0,self.temp.name)
        thread=threading.Thread(target=self.server.serve_forever,daemon=True);thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)

    def request(self,path,body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        h={'Authorization':'Bearer '+self.server.token,'Origin':self.server.origin,'Content-Type':'application/json'}
        h.update(headers or {})
        c.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,h)
        r=c.getresponse();payload=r.read();c.close();return r.status,payload

    def test_archive_api(self):
        project=self.server.store.create('Archivo ficticio')['id']
        self.server.assistant.active=(project,'test')
        self.assertEqual(self.request('/api/project/archive',dict(project=project,archived=True))[0],409)
        self.server.assistant.active=None
        self.assertEqual(self.request('/api/project/archive',dict(project=project,archived='true'))[0],400)
        self.assertEqual(self.request('/api/project/archive',dict(project=project,archived=True))[0],200)
        data=json.loads(self.request('/api/projects')[1])
        self.assertEqual(data['projects'],[]);self.assertEqual(data['archived'][0]['id'],project)
        self.assertEqual(self.request('/api/project/archive',dict(project=project,archived=False))[0],200)
        data=json.loads(self.request('/api/projects')[1]);self.assertEqual(data['archived'],[])
        self.assertEqual(data['projects'][0]['id'],project)

    def test_conversation_reset_preserves_archive_and_clears_all_contexts(self):
        from src.workbench_ai import portable_history
        from src.workbench_realtime import context
        from test_desktop_features import MODELS
        store=self.server.store;project=store.create('Chats ficticios',True)['id']
        data=store.load(project)
        data['runs']=[dict(id='old',mode='chat',purpose='novel',status='completed',prompt='Pregunta antigua',text='Respuesta antigua',sources=[])]
        data.update(thread='old-thread',context_key='old-key');store.persist(data)
        before={p:p.read_bytes() for p in store.root.rglob('*.md')}
        self.server.assistant.active=(project,'test')
        self.assertEqual(self.request('/api/thread/reset',dict(project=project))[0],409)
        self.server.assistant.active=None
        self.assertEqual(self.request('/api/thread/reset',dict(project=project,draft=42))[0],400)
        status,body=self.request('/api/thread/reset',dict(project=project,draft='Texto sin enviar'))
        self.assertEqual(status,200);data=json.loads(body)
        self.assertIsNone(data['thread']);self.assertIsNone(data['context_key']);self.assertEqual(data['history_start'],1)
        self.assertEqual(data['conversations'][0]['draft'],'Texto sin enviar')
        self.assertEqual(data['conversations'][0]['end'],1)
        self.assertEqual(data['runs'][0]['text'],'Respuesta antigua')
        self.assertEqual(context(data)['recent_turns'],[])
        self.assertNotIn('Respuesta antigua',portable_history(data,dict(id='new',purpose='novel'),data['documents']))
        self.request('/api/thread/reset',dict(project=project))
        self.assertEqual(len(store.load(project)['conversations']),1)
        self.assertEqual(before,{p:p.read_bytes() for p in store.root.rglob('*.md')})
        # El catálogo del usuario valida ambos selectores antes de guardar.
        self.server.account.set(models=MODELS,status='connected')
        for model,effort,status in [('modelo-b','low',200),('modelo-b','high',400),('missing','low',400)]:
            self.assertEqual(self.request('/api/project/team',dict(project=project,preferences=dict(model=model,effort=effort,max_agents=2)))[0],status)
        self.assertEqual(store.load(project)['team_preferences']['effort'],'low')
        # Recupera el historial de versiones previas que solo tenían history_start.
        data=store.load(project);data.pop('schema_version');del data['conversations'];store.persist(data)
        self.assertEqual(store.load(project)['conversations'][0]['end'],1)

    def test_second_server_cannot_open_same_data(self):
        with self.assertRaises(BlockingIOError):
            AppServer(0,self.temp.name)

    def test_host_origin_auth_and_api(self):
        for headers in ({'Authorization':'Bearer invalid'},{'Origin':'https://evil.example'},{'Host':'evil.example'}):
            status,_=self.request('/api/projects',headers=headers);self.assertIn(status,(401,403))
        status,body=self.request('/api/projects',{'title':'Proyecto HTTP','demo':True})
        self.assertEqual(status,200)
        project=json.loads(body)['id']
        status,body=self.request('/api/projects/'+project);self.assertEqual(status,200)
        doc=json.loads(body)['documents'][0]
        status,_=self.request('/api/document/save',{'project':project,'document':doc['id'],'hash':'stale','content':'no'})
        self.assertEqual(status,409)
        status,body=self.request('/api/projects/'+project+'/export');self.assertEqual(status,200);self.assertTrue(body.startswith(b'PK'))
        status,_=self.request('/api/projects/../../etc/passwd');self.assertIn(status,(400,404))
        status,_=self.request('/api/run',{'project':project,'mode':'shell','prompt':'no'})
        self.assertEqual(status,400)


if __name__=='__main__':unittest.main()
