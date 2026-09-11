"""Importación y espacios con árboles ficticios, sin IA ni originales privados."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.workbench_store import Store, Problem, MAX_TEXT
from src.workbench_workspace import Workspace, import_preview, import_documents
from src.workbench_modes import detect_language
from src.app import AppServer
import test_workbench


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.original=self.root/'original';self.original.mkdir()
        (self.original/'manuscript').mkdir();(self.original/'manuscript'/'cuento.md').write_text('Una obra ficticia.\n')
        (self.original/'STYLE.md').write_text('Voz de prueba.')
        (self.original/'.env').write_text('fictional-secret')
        (self.original/'cover.png').write_bytes(b'fake-image')
        self.store=Store(self.root/'projects')

    def test_copy_selection_and_boundaries(self):
        preview=import_preview(str(self.original))
        self.assertEqual({f['name'] for f in preview['files']},{'STYLE.md','manuscript/cuento.md'})
        docs=import_documents(str(self.original),['manuscript/cuento.md','STYLE.md'])
        project=self.store.create('Copia',workflow='guided',documents=docs)
        snapshot=self.store.snapshot(project['id']);self.assertEqual(len(snapshot['documents']),2)
        self.assertFalse(any(d['selected'] for d in snapshot['documents']))
        self.assertEqual(snapshot['documents'][0]['role'],'manuscrito')
        first=snapshot['documents'][0];self.store.save_document(project,first['id'],'Solo cambia la copia',first['hash'])
        self.assertEqual((self.original/'manuscript/cuento.md').read_text(),'Una obra ficticia.\n')
        for names in [[],['../STYLE.md'],['.env'],['STYLE.md','STYLE.md'],['cover.png']]:
            with self.assertRaises(Problem):import_documents(str(self.original),names)
        (self.original/'linked.md').symlink_to(self.original/'STYLE.md')
        with self.assertRaises(Problem):import_documents(str(self.original),['linked.md'])
        (self.original/'invalid.txt').write_bytes(b'\xff')
        with self.assertRaises(UnicodeError):import_documents(str(self.original),['invalid.txt'])
        (self.original/'large.txt').write_bytes(b'x'*(MAX_TEXT+1))
        with self.assertRaises(Problem):import_documents(str(self.original),['large.txt'])

    def test_translation_requires_original_and_preserves_partition(self):
        text=('El viento volvió. Ella estaba en la casa, pero él no había llegado.\n\n'*500)
        data=self.store.create('Edición',purpose='translation',initial_idea='Ignorar',documents=[dict(name='Obra.md',content=text)],translation=dict(source=0,source_language='Español',target_language='Inglés'))
        docs=self.store.snapshot(data['id'])['documents']
        self.assertEqual(''.join(d['content'] for d in docs),text)
        self.assertEqual(len(docs), 1)
        self.assertEqual(sum(d['selected'] for d in docs),1)
        self.assertEqual(data['translation_config']['source'],docs[0]['id'])
        self.assertEqual((data['workflow'],data['initial_idea']),('guided',''))
        before=self.store.list_projects()
        for config in [None,dict(source=0,source_language='es',target_language='es'),dict(source=1,source_language='es',target_language='en')]:
            with self.assertRaises(Problem):self.store.create('Inválido',purpose='translation',documents=[dict(name='X',content='Texto')],translation=config)
        with self.assertRaises(Problem):self.store.create('Vacío',purpose='translation',translation=dict(source=0,source_language='es',target_language='en'))
        with patch.object(self.store,'add_document',side_effect=OSError('disco')):
            with self.assertRaises(OSError):self.store.create('No parcial',documents=[dict(name='X',content='Texto')])
        self.assertEqual(self.store.list_projects(),before)

    def test_detection_suggests_without_inventing_language(self):
        samples={
            'Español':'Ella estaba en la casa cuando él dijo que sus amigos habían pasado por el jardín, pero no había una carta para los niños.',
            'Inglés':'She was with her friend and he said that the letter had arrived from his mother. They were not sure what it meant.',
            'Portugués':'Ela não tinha uma casa mas ele disse que sua mãe estava esperando pela carta. Você sabe que seu pai chegou pelo jardim.',
            'Francés':'Elle était dans une maison avec les enfants mais il avait des lettres pour lui. Ses amis sont arrivés du village.',
            'Italiano':'Lei aveva una casa nella città e lui disse che gli amici della famiglia non sono arrivati. Le luci delle finestre erano accese.',
            'Alemán':'Der Mann war mit einer Frau und sie hatte eine Tasche. Er sagte nicht viel. Das Kind sah die Blumen in dem Garten.'}
        for language,text in samples.items():self.assertEqual(detect_language(text),language)
        for text in ['Te quiero','abc '*100,'これは日本語の文章です。'*30,samples['Español']+' '+samples['Inglés']]:self.assertEqual(detect_language(text),'')

    def test_workspace_create_reopen_reject_original_and_missing(self):
        default=self.root/'default';workspace=Workspace(default)
        with self.assertRaises(Problem):workspace.choose(str(self.original))
        for name in ['../oops','bad/name','CON','tail.']:
            with self.assertRaises(Problem):workspace.choose(str(self.root),name)
        result=workspace.choose(str(self.root),'Nueva biblioteca')
        target=self.root/'Nueva biblioteca';self.assertEqual(result['active'],str(default));self.assertTrue(result['restart'])
        self.assertEqual(Workspace(default).active,target)
        server=AppServer(0,default)
        try:
            self.assertEqual(server.store.root,target)
            project=server.store.create('Persistido')
            with self.assertRaises(BlockingIOError):AppServer(0,default)
        finally:server.server_close()
        server=AppServer(0,default)
        try:self.assertEqual(server.store.load(project['id'])['title'],'Persistido')
        finally:server.server_close()
        target.rename(self.root/'desconectada')
        fallback=Workspace(default);self.assertEqual(fallback.active,default);self.assertTrue(fallback.warning)
        self.assertFalse(target.exists())
        fallback.choose(str(default));self.assertEqual(Workspace(default).active,default)


class WorkspaceHTTP(unittest.TestCase):
    setUp=test_workbench.HTTPTests.setUp
    request=test_workbench.HTTPTests.request

    def test_translation_validation_and_detection_routes(self):
        self.assertEqual(self.request('/api/projects',dict(title='Sin original',purpose='translation'))[0],400)
        self.assertEqual(self.request('/api/translation/detect',dict(text='Te quiero'))[0],200)
        self.assertEqual(self.request('/api/workspace')[0],200)
        self.assertEqual(self.request('/api/import/preview',dict(path='relative'))[0],400)
        self.assertEqual(self.request('/api/projects',dict(title='X',import_folder='invalid'))[0],400)
