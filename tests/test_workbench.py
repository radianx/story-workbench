import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from app import AppServer
from workbench_ai import Assistant
from workbench_store import Store, Problem, digest


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.project = self.store.create('Ficción de prueba', True)['id']

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
        with self.assertRaises(Problem):
            assistant.start(self.project,'chat','Pregunta')
        self.assertIsNone(assistant.active)


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
