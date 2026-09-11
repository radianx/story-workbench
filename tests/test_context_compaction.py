"""Compaction invalidates usage; synthetic App Server events, no account calls."""
import asyncio
import tempfile
import unittest
from unittest.mock import patch
from src.workbench_ai import Assistant
from src.workbench_store import Store
from test_codex_images import ImageServer


class CompactionTests(unittest.TestCase):
    def test_scoped_events_and_fresh_measurement(self):
        def event(method, **values):
            return dict(method=method, params=dict(threadId='thread-test', turnId='turn-test', **values))
        def usage(tokens):
            return event('thread/tokenUsage/updated', tokenUsage=dict(last=dict(totalTokens=tokens), modelContextWindow=1000))
        for legacy in (False, True):
            for refresh in (False, True):
                class Server(ImageServer):
                    async def rpc(self, method, params):
                        result = await super().rpc(method, params)
                        if method == 'turn/start':
                            wrong = event('thread/compacted')
                            wrong['params']['turnId'] = 'wrong-turn'
                            other = event('thread/compacted')
                            other['params']['threadId'] = 'wrong-thread'
                            self.events = [usage(1260), wrong, other]
                            if legacy:
                                self.events += [event('thread/compacted')]
                            else:
                                self.events += [event('item/started', item=dict(type='contextCompaction', id='compact')),
                                                usage(1300),
                                                event('item/completed', item=dict(type='contextCompaction', id='compact'))]
                            if refresh:
                                self.events += [usage(200)]
                            self.events += [event('turn/completed', turn=dict(id='turn-test', status='completed'))]
                        return result
                with self.subTest(legacy=legacy, refresh=refresh), tempfile.TemporaryDirectory() as directory:
                    store = Store(directory); project = store.create('Ficción')['id']; assistant = Assistant(store)
                    with patch('threading.Thread.start'):
                        assistant.start(project, 'chat', 'Pregunta ficticia', False)
                    run = store.load(project)['runs'][-1]
                    with patch('src.workbench_ai.Server', Server), patch('src.workbench_ai.shutil.which', return_value='/usr/bin/true'), patch.object(assistant, 'update', wraps=assistant.update) as updates:
                        asyncio.run(assistant.execute(project, run, []))
                    values = [call.kwargs for call in updates.call_args_list if 'context_usage' in call.kwargs]
                    self.assertEqual(values[0]['context_usage']['tokens'], 1260)
                    self.assertEqual(sum(v.get('context_pending') is True for v in values), 1 if legacy else 2)
                    self.assertFalse(any(v.get('context_usage', {}).get('tokens') == 1300 for v in values if v.get('context_usage')))
                    saved = store.load(project)['runs'][-1]
                    self.assertEqual(saved['context_usage'], dict(tokens=200, window=1000) if refresh else None)
                    self.assertEqual(saved['context_pending'], not refresh)
                    self.assertEqual(saved['status'], 'completed')
