import json
import tempfile
import unittest
from unittest.mock import patch
from src.workbench_store import Store, Problem
from src.workbench_ai import Assistant
import src.workbench_modes as modes
import test_workbench

QUESTION=dict(message='Falta decidir el vínculo.',question='¿Afecto amistoso o romántico?',quote='Te quiero',draft='',
              options=[dict(wording='I care about you',effect='Afecto sin declaración romántica.'),dict(wording='I love you',effect='Puede sugerir amor romántico.')])
DRAFT=dict(message='Conservé el afecto amistoso.',question='',quote='',draft='“I care about you,” she said.',options=[])

class Modes(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.store=Store(temp.name);self.project=self.store.create('Traducción ficticia',workflow='guided',purpose='translation',documents=[dict(name='Original.md',role='manuscrito',content='—Te quiero —dijo.')],translation=dict(source=0,source_language='es',target_language='en'))['id']
        self.source=self.store.snapshot(self.project)['documents'][0]
        self.config=dict(source=self.source['id'],source_language='Español rioplatense',target_language='Inglés estadounidense',intent='Conservar intención',glossary='')
        modes.configure_translation(self.store,self.store.load(self.project),self.config)
        self.assistant=Assistant(self.store)

    def result(self,value):
        with patch('src.workbench_ai.threading.Thread.start'):
            result=self.assistant.start(self.project,'translate','Traducción ficticia',False)
        data=self.store.load(self.project);run=next(r for r in data['runs'] if r['id']==result['id'])
        run.update(status='completed',text=value['message'],translation_result=modes.validate_translation(value,run['translation_context']))
        self.store.persist(data);self.assistant.active=None
        return run

    def test_author_criterion_separate_copy_review_and_export(self):
        run=self.result(QUESTION)
        with self.assertRaises(Problem):self.result(DRAFT)
        with self.assertRaises(Problem):modes.accept_translation(self.store,self.store.load(self.project),run['id'],'No aprobar')
        modes.answer_translation(self.store,self.store.load(self.project),run['id'],'Afecto amistoso, sin romance.')
        modes.answer_translation(self.store,self.store.load(self.project),run['id'],'Afecto amistoso, sin romance.')
        self.assertEqual(len(self.store.load(self.project)['decisions']),1)
        run=self.result(DRAFT);doc=modes.accept_translation(self.store,self.store.load(self.project),run['id'],'I care about you. — Versión del autor.')
        self.assertEqual(doc['role'],'traducción');self.assertFalse(doc['selected']);self.assertEqual(doc['translation_status'],'reviewed')
        self.assertEqual(self.store.document(self.store.load(self.project),self.source['id'])['content'],self.source['content'])
        self.assertEqual(modes.accept_translation(self.store,self.store.load(self.project),run['id'],'No pisar')['id'],doc['id'])
        edited=self.store.save_document(self.store.load(self.project),doc['id'],'A revised translation.',doc['hash'])
        self.assertEqual(edited['translation_status'],'revise')
        with self.assertRaises(Problem):modes.translation_edition(self.store.snapshot(self.project))
        with self.assertRaises(Problem):modes.review_translation(self.store,self.store.load(self.project),doc['id'],doc['hash'],self.source['hash'])
        modes.review_translation(self.store,self.store.load(self.project),doc['id'],edited['hash'],self.source['hash'])
        edition=modes.translation_edition(self.store.snapshot(self.project))
        self.assertEqual(edition['documents'][0]['content'],'A revised translation.')
        self.assertEqual(len(edition['documents']),1)

    def test_source_brief_and_criteria_conflicts(self):
        run=self.result(DRAFT)
        data=self.store.load(self.project);data['decisions'].append(dict(text='Criterio nuevo',status='accepted'));self.store.persist(data)
        with self.assertRaises(Problem):modes.accept_translation(self.store,self.store.load(self.project),run['id'],DRAFT['draft'])
        run=self.result(DRAFT)
        self.store.save_document(self.store.load(self.project),self.source['id'],'Otro original.',self.source['hash'])
        with self.assertRaises(Problem):modes.accept_translation(self.store,self.store.load(self.project),run['id'],DRAFT['draft'])
        self.assertEqual(len(self.store.load(self.project)['documents']),1)
        self.assertNotEqual(modes.brief_hash(self.config),modes.brief_hash({**self.config,'glossary':'Nuevo criterio'}))
        self.assertEqual(modes.brief_hash(self.config),modes.brief_hash({**self.config,'source':'otra unidad'}))

    def test_validation_and_context_boundaries(self):
        context=dict(original=self.source['content'])
        for invalid in (None,{**QUESTION,'draft':'Traducción prematura'},{**QUESTION,'quote':'Cita inventada'},
                        {**QUESTION,'options':[]},{**DRAFT,'draft':''},{**QUESTION,'options':['x']}):
            with self.assertRaises(Problem):modes.validate_translation(invalid,context)
        for invalid in (None,{**self.config,'source_language':''},{**self.config,'target_language':5}):
            with self.assertRaises(Problem):modes.configure_translation(self.store,self.store.load(self.project),invalid)
        data=self.store.load(self.project);data['documents'][0]['selected']=False;self.store.persist(data)
        with self.assertRaises(Problem):self.assistant.start(self.project,'translate','Prueba')
        with self.assertRaises(Problem):self.assistant.start(self.project,'draft','No esquivar revisión')
        data['documents'][0]['selected']=True;self.store.persist(data)
        original = 'Capítulo completo. ' * 20000
        self.store.save_document(data,self.source['id'],original,self.source['hash'])
        translated = 'Complete chapter. ' * 22000
        run = self.result({**DRAFT, 'draft': translated})
        self.assertEqual(run['translation_context']['original'], original)
        copy = modes.accept_translation(self.store,self.store.load(self.project),run['id'],translated)
        self.assertEqual(copy['content'], translated)
        self.assertEqual(self.store.document(self.store.load(self.project),self.source['id'])['content'], original)
        from src.workbench_ai import task_text
        prompt = task_text(run, [self.store.document(self.store.load(self.project),self.source['id'])], {}, [])
        self.assertEqual(prompt.count(original), 1)

    def test_rpg_and_legacy_defaults(self):
        data=self.store.create('Mesa ficticia',workflow='guided',purpose='rpg');project=data['id']
        self.assertEqual(data['documents'],[])
        assistant=Assistant(self.store)
        with patch('src.workbench_ai.threading.Thread.start'):
            assistant.start_interview(project)
        run=self.store.load(project)['runs'][0]
        self.assertEqual(run['purpose'],'rpg');self.assertFalse(run['skill'])
        data=self.store.load(project);data['runs'].append(dict(id='world1',mode='draft',purpose='rpg',status='completed',text='# Un puerto flotante\n\nReglas caseras provisionales.'));self.store.persist(data)
        doc=self.store.save_draft(data,'world1');self.assertEqual(doc['role'],'plan');self.assertFalse(doc['selected'])
        self.assertEqual(self.store.save_draft(self.store.load(project),'world1')['id'],doc['id'])
        data=self.store.load(project);data.pop('schema_version');data.pop('purpose');self.store.persist(data)
        self.assertEqual(self.store.load(project)['purpose'],'novel')
        with self.assertRaises(Problem):self.store.create('Inválido',purpose='combat')

class ModesHTTP(unittest.TestCase):
    setUp=test_workbench.HTTPTests.setUp
    request=test_workbench.HTTPTests.request
    def test_routes_keep_private_copy_and_export_metadata(self):
        _,body=self.request('/api/projects',dict(title='Edición ficticia',workflow='guided',purpose='translation',documents=[dict(name='Original.md',content='Te quiero')],translation=dict(source=0,source_language='es',target_language='en')));project=json.loads(body)['id']
        source=json.loads(body)['documents'][0]['id']
        config=dict(source=source,source_language='es',target_language='en',intent='',glossary='')
        self.assertEqual(self.request('/api/translation/config',dict(project=project,config=config))[0],200)
        for route in ('answer','accept','review'):
            self.assertIn(self.request('/api/translation/'+route,dict(project=project))[0],(400,404,409))
        self.assertEqual(self.request('/api/projects/'+project+'/translation.md')[0],400)
        self.assertEqual(self.request('/api/project/purpose',dict(project=project,purpose='rpg'))[0],200)
        self.assertEqual(self.request('/api/project/purpose',dict(project=project,purpose='combat'))[0],400)
