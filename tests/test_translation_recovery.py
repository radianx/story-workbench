"""Long and interrupted turns with a virtual clock, no provider or manuscript access."""
import asyncio
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from src.workbench_ai import Assistant, task_text
from src.workbench_store import Store, Problem
from src.workbench_modes import partial_translation, accept_translation
from test_desktop_features import MODELS


class RecoveryServer:
    script=[];clock=0;assistant=None;silent_cancel=False
    def __init__(self,*args,**kwargs):self.events=[];self.steps=iter(type(self).script)
    async def __aenter__(self):return self
    async def __aexit__(self,*args):pass
    async def rpc(self,method,params):
        if method=='model/list':return dict(data=MODELS,nextCursor=None)
        if method in ('thread/start','thread/resume'):return dict(thread={'id':'thread'},model=params['model'],modelProvider='openai')
        if method=='turn/start':return {'turn':{'id':'turn'}}
        if method=='turn/interrupt':return {}
        raise AssertionError(method)
    async def read(self):
        seconds,kind,value=next(self.steps)
        type(self).clock+=seconds
        if kind=='idle':raise asyncio.TimeoutError
        if kind=='cancel':
            self.assistant.cancel.set();raise asyncio.TimeoutError
        if kind=='disconnect':raise ConnectionError('fictitious disconnection')
        if kind=='delta':return dict(method='item/agentMessage/delta',params=dict(threadId='thread',turnId='turn',delta=value))
        return dict(method='turn/completed',params=dict(threadId='thread',turn=dict(id='turn',status=value)))


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.store=Store(temp.name)
        self.project=self.store.create('Ficción',purpose='translation',documents=[dict(name='Escena',content='El río volvió.')],translation=dict(source=0,source_language='es',target_language='en'))['id']
        self.assistant=Assistant(self.store)
        RecoveryServer.clock=0;RecoveryServer.assistant=self.assistant

    def start(self,previous=None):
        with patch('threading.Thread.start'):
            self.assistant.start(self.project,'translate','Traducir',False,False,previous)
        data=self.store.load(self.project)
        return data['runs'][-1],[self.store.document(data,d['id']) for d in data['documents'] if d['selected']]

    def execute(self,script):
        run,docs=self.start();RecoveryServer.script=script
        with patch.dict(os.environ,{'STORY_CODEX_BINARY':sys.executable}),patch('src.workbench_ai.Server',RecoveryServer),patch('src.workbench_ai.monotonic',side_effect=lambda:RecoveryServer.clock),patch.object(self.assistant,'update',wraps=self.assistant.update) as updates:
            self.assistant.worker(self.project,run,docs)
        return self.store.snapshot(self.project)['runs'][-1],updates

    def test_long_turn_waits_and_finishes(self):
        result=dict(message='Borrador revisable.',question='',quote='',options=[],draft='The river returned.')
        run,updates=self.execute([(61,'idle',None),(601,'delta',json.dumps(result)),(1,'done','completed')])
        self.assertEqual(run['status'],'completed')
        self.assertEqual(run['translation_result']['draft'],result['draft'])
        self.assertTrue(any(c.kwargs.get('waiting') for c in updates.call_args_list))
        self.assertFalse(run['waiting'])

    def test_disconnect_preserves_partial_and_resume_checks_source(self):
        raw='{"message":"Borrador","draft":"The river\\nreturned'
        run,_=self.execute([(0.1,'delta',raw),(0.01,'disconnect',None)])
        self.assertEqual(run['status'],'failed');self.assertIn('conexión',run['error'])
        self.assertEqual(run['text'],raw);self.assertEqual(run['translation_partial'],'The river\nreturned')
        with self.assertRaises(Problem):accept_translation(self.store,self.store.load(self.project),run['id'],'Not complete')
        resumed,docs=self.start(run['id'])
        self.assertEqual(resumed['continued_from'],run['id'])
        self.assertIn('The river\\nreturned',task_text(resumed,docs,{},[]))
        self.assertEqual(resumed['translation_context'],run['translation_context'])
        self.assistant.active=None
        data=self.store.load(self.project);doc=docs[0];self.store.save_document(data,doc['id'],'Otro original',doc['hash'])
        with self.assertRaises(Problem):self.start(run['id'])

    def test_invalid_json_and_unacknowledged_cancellation(self):
        raw='{"draft":"The river'
        run,_=self.execute([(1,'delta',raw),(1,'done','completed')])
        self.assertIn('formato',run['error']);self.assertEqual(run['text'],raw)
        run,_=self.execute([(1,'delta',raw),(1,'cancel',None),(6,'idle',None)])
        self.assertEqual(run['status'],'interrupted');self.assertEqual(run['text'],raw)
        self.assertIsNone(self.assistant.active)

    def test_partial_escapes(self):
        for text,expected in [('{}',''),('{"draft":"a\\n\\u00e1','a\ná'),('{"draft":"a\\u00','a'),('{"draft":"a\\','a'),('{"draft":"a\\ud83d','a'),('{"draft":"a\\ud83d\\ude00"}','a😀'),('{"draft":"a", "message":"x"}','a')]:
            self.assertEqual(partial_translation(text),expected)
