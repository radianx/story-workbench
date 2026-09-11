"""Codex protocol attachments, original bytes and path isolation; no provider calls."""
import asyncio
import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.workbench_ai import Assistant, editor_overrides
from src.workbench_images import receive_codex_image
from src.workbench_store import Store, Problem
from test_desktop_features import MODELS
from test_images import png


class ImageServer:
    overrides = []
    def __init__(self, cwd, overrides, **kwargs):
        type(self).overrides = overrides
        self.events = []
    async def __aenter__(self): return self
    async def __aexit__(self, *_): pass
    async def rpc(self, method, params):
        if method == 'model/list': return {'data': MODELS, 'nextCursor': None}
        if method in ('thread/start', 'thread/resume'):
            assert 'image_gen' in params['developerInstructions']
            return dict(thread={'id': 'thread-test'}, modelProvider='openai', model=params['model'])
        if method == 'turn/start':
            item = dict(type='imageGeneration', id='call-test', status='completed', result=base64.b64encode(png()).decode())
            event = dict(method='item/completed', params=dict(threadId='thread-test', turnId='turn-test', item=item))
            self.events = [
                dict(method='item/completed', params={**event['params'], 'threadId':'wrong-thread'}),
                dict(method='item/completed', params={**event['params'], 'turnId':'wrong-turn'}),
                event, event,
                dict(method='item/agentMessage/delta', params=dict(threadId='thread-test', turnId='turn-test', delta='Imagen provisional.')),
                dict(method='turn/completed', params=dict(threadId='thread-test', turn=dict(id='turn-test', status='completed')))]
            return {'turn': {'id': 'turn-test'}}
        raise AssertionError(method)


class CodexImagesTest(unittest.TestCase):
    def test_stream_attachment_persistence_and_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory); project = store.create('Ficción visual')['id']; assistant = Assistant(store)
            with patch('threading.Thread.start'):
                assistant.start(project, 'chat', 'Generá un faro violeta.', False)
            run = store.load(project)['runs'][-1]
            with patch('src.workbench_ai.Server', ImageServer), patch('src.workbench_ai.shutil.which', return_value='/usr/bin/true'):
                asyncio.run(assistant.execute(project, run, []))
                self.assertNotIn('features.image_generation=true', editor_overrides())
            data = store.snapshot(project)
            self.assertEqual(data['runs'][-1]['status'], 'completed')
            self.assertEqual(len(data['images']), 1)
            image = data['images'][0]
            self.assertEqual(data['runs'][-1]['attachments'], [image['id']])
            self.assertEqual(store.path(project,'images',image['file']).read_bytes(), png())
            self.assertNotIn('result', json.dumps(data)); self.assertFalse(data.get('production'))
            for setting in ('features.image_generation=true', 'features.shell_tool=false', 'features.code_mode=false', 'permissions.storyworkbench.network.enabled=false'):
                self.assertIn(setting, ImageServer.overrides)
            store.reset_conversation(store.load(project))
            self.assertEqual(store.snapshot(project)['runs'][-1]['attachments'], [image['id']])

    def test_invalid_payload_and_saved_path_isolation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'CODEX_HOME': directory}):
            store = Store(Path(directory)/'projects'); project = store.create('Imagen')['id']
            run = dict(id='a'*32, prompt='Ficción', status='completed')
            data = store.load(project); data['runs'].append(run); store.persist(data)
            item = dict(type='imageGeneration', id='call-test', result='', status='completed')
            root = Path(directory)/'generated_images'/'thread-test'; root.mkdir(parents=True)
            source = root/'call-test.png'; source.write_bytes(png())
            for bad in (dict(result='garbage'), dict(result=base64.b64encode(b'<svg/>').decode()),
                        dict(savedPath=str(Path(directory)/'secret.png')), dict(savedPath=str(source.parent/'..'/'call-test.png')),
                        dict(id='../call-test'), dict(failure={'type':'usageLimitExceeded'})):
                with self.subTest(bad=list(bad)), self.assertRaises(Exception):
                    receive_codex_image(store, project, run, {**item, **bad}, 'thread-test')
            source.unlink(); source.symlink_to(Path(directory)/'private.png')
            with self.assertRaises(Problem): receive_codex_image(store, project, run, {**item, 'savedPath':str(source)}, 'thread-test')
            source.unlink(); source.write_bytes(png())
            record = receive_codex_image(store, project, run, {**item, 'savedPath':str(source)}, 'thread-test')
            self.assertTrue(record['provisional'])
            self.assertEqual(store.path(project,'images',record['file']).read_bytes(), png())
