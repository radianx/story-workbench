import io
import json
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from xml.etree import ElementTree as ET
from src.workbench_store import Store, Problem
from src.workbench_export import export_book
from src.workbench_ai import Assistant
import test_workbench


class Planning(unittest.TestCase):
    def test_plan_order_review_invalidation_and_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);data=store.create('Ficción & orden',True);project=data['id']
            docs=[d for d in store.snapshot(project)['documents'] if d['role']=='manuscrito']
            doc=docs[0]
            store.planning(data,doc['id'],dict(synopsis='La radio llama.',pov='Inés',stage='reviewed',hash=doc['hash']))
            store.reorder(data,[d['id'] for d in reversed(docs)])
            snapshot=store.snapshot(project)
            self.assertEqual([d['id'] for d in snapshot['documents'] if d['role']=='manuscrito'],[d['id'] for d in reversed(docs)])
            self.assertEqual(store.document(data,doc['id'])['stage'],'reviewed')
            store.save_document(data,doc['id'],doc['content']+'\nTexto nuevo & <seguro>\x01',doc['hash'])
            self.assertEqual(store.snapshot(project)['documents'][-1]['stage'],'revise')
            with self.assertRaises(Problem):store.planning(data,doc['id'],dict(stage='reviewed',hash=doc['hash']))
            for order in (None, [doc['id']]*2, [doc['id']], [d['id'] for d in data['documents']], [{'id':doc['id']}]*2):
                with self.assertRaises(Problem):store.reorder(data,order)
            for invalid in (dict(stage='canon'),dict(stage='reviewed',synopsis='x'*4001),dict(stage='planned',pov=42)):
                with self.assertRaises(Problem):store.planning(data,doc['id'],{**invalid,'hash':store.document(data,doc['id'])['hash']})
            snapshot=store.snapshot(project)
            md,_=export_book(snapshot,'book.md')
            self.assertLess(md.index(b'El cuarto de radio'),md.index(b'La \xc3\xbaltima luz'))
            self.assertNotIn(b'Canon aprobado',md)
            docx,mime=export_book(snapshot,'book.docx')
            self.assertIn('wordprocessingml',mime)
            with zipfile.ZipFile(io.BytesIO(docx)) as archive:
                for name in archive.namelist():ET.fromstring(archive.read(name))
                text=''.join(ET.fromstring(archive.read('word/document.xml')).itertext())
                self.assertIn('Texto nuevo & <seguro>',text)
                self.assertNotIn('Canon aprobado',text)
                self.assertLess(text.index('El cuarto de radio'),text.index('La última luz'))
            empty=store.create('Vacío')
            with self.assertRaises(Problem):export_book(store.snapshot(empty['id']),'book.md')
            blank=store.document(empty,empty['documents'][0]['id'])
            with self.assertRaises(Problem):store.planning(empty,blank['id'],dict(stage='reviewed',hash=blank['hash']))

    def test_draft_saved_once_and_plan_context_is_selected_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);data=store.create('Ficción');project=data['id']
            data['runs']=[dict(id='draft1',mode='draft',status='completed',text='Una biblioteca flotaba.')];store.persist(data)
            first=store.save_draft(data,'draft1')
            second=store.save_draft(store.load(project),'draft1')
            self.assertEqual(first['id'],second['id'])
            self.assertEqual(len(store.load(project)['documents']),2)
            # Recuperar incluso si el cierre ocurrió entre ambos guardados de metadatos.
            data=store.load(project);del data['runs'][0]['saved_document'];store.persist(data)
            self.assertEqual(store.save_draft(data,'draft1')['id'],first['id'])
            private=store.add_document(project,'Ficha no seleccionada','plan','Secreto',selected=False)
            data=store.load(project);store.planning(data,first['id'],dict(synopsis='Biblioteca en el mar',pov='Mara',stage='drafting',hash=first['hash']))
            assistant=Assistant(store)
            with patch('src.workbench_ai.threading.Thread.start'):
                assistant.start(project,'draft','Una escena')
                run=store.load(project)['runs'][-1]
                self.assertNotIn(private['id'],run['source_texts'])
                self.assertEqual(run['sources'][-1]['pov'],'Mara')
            data=store.load(project);d=store.document(data,first['id']);store.save_document(data,d['id'],'x'*59000,d['hash'])
            data=store.load(project);d=store.document(data,first['id']);store.planning(data,d['id'],dict(synopsis='s'*2000,pov='',stage='drafting',hash=d['hash']))
            assistant.active=None
            with patch('src.workbench_ai.threading.Thread.start'):
                assistant.start(project,'draft','Capítulo completo')
            self.assertIn('x'*59000, store.load(project)['runs'][-1]['source_texts'].values())


class PlanningHTTP(unittest.TestCase):
    setUp = test_workbench.HTTPTests.setUp
    request = test_workbench.HTTPTests.request
    # Reutilizar el servidor y cliente de seguridad ya comprobados.
    def test_planning_endpoints(self):
        _,body=self.request('/api/projects',{'title':'Plan HTTP','demo':True});project=json.loads(body)['id']
        _,body=self.request('/api/projects/'+project);data=json.loads(body);doc=data['documents'][0]
        self.assertEqual(self.request('/api/project/goal',{'project':project,'goal':50000})[0],200)
        for goal in (True,-1,2_000_001,'100',1.2):self.assertEqual(self.request('/api/project/goal',{'project':project,'goal':goal})[0],400)
        self.assertEqual(self.request('/api/document/planning',{'project':project,'document':doc['id'],'planning':{'synopsis':'Plan','pov':'Inés','stage':'reviewed','hash':doc['hash']}})[0],200)
        ids=[d['id'] for d in data['documents'] if d['role']=='manuscrito']
        self.assertEqual(self.request('/api/project/order',{'project':project,'order':ids[::-1]})[0],200)
        self.assertEqual(self.request('/api/projects/'+project+'/book.docx')[0],200)
        self.assertEqual(self.request('/api/projects/'+project+'/book.md')[0],200)
        status,body=self.request('/api/projects/'+project+'/export')
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            manifest=json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['word_goal'],50000)
            self.assertEqual(manifest['documents'][-1]['pov'],'Inés')
        self.assertEqual(self.request('/api/run/save-draft',{'project':project,'run':'missing'})[0],409)
