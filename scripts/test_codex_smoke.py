"""Comprobaciones sin red ni cuenta: python3 -m unittest discover -s scripts."""
import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from codex_smoke import Server, SmokeError, chatgpt_only, launch_settings


class SmokeTests(unittest.TestCase):
    def test_account_and_launch_guards(self):
        chatgpt_only({'account': {'type': 'chatgpt'}})
        for account in (None, {}, {'type': 'apiKey'}, {'type': 'chatgptAuthTokens'}):
            with self.assertRaises(SmokeError):
                chatgpt_only({'account': account})
        with tempfile.TemporaryDirectory() as directory:
            env = {'CODEX_HOME': directory, 'OPENAI_API_KEY': 'fake',
                   'OPENAI_BASE_URL': 'https://invalid.example', 'PATH': '/bin'}
            with patch.dict('os.environ', env, clear=True):
                command, child_env = launch_settings()
                self.assertNotIn('OPENAI_API_KEY', child_env)
                self.assertNotIn('OPENAI_BASE_URL', child_env)
                self.assertIn('forced_login_method="chatgpt"', command)
                self.assertIn('sandbox_mode="read-only"', command)
                Path(directory, 'config.toml').write_text('[model_providers.openai]\n')
                with self.assertRaises(SmokeError):
                    launch_settings()

    def test_interleaving_completion_and_failure(self):
        async def check():
            server = Server('/tmp')
            server.events = [
                {'method': 'item/agentMessage/delta', 'params': {
                    'threadId': 'other', 'turnId': 't', 'delta': 'wrong'}},
                {'method': 'item/agentMessage/delta', 'params': {
                    'threadId': 'h', 'turnId': 'old', 'delta': 'wrong'}},
                {'method': 'item/agentMessage/delta', 'params': {
                    'threadId': 'h', 'turnId': 't', 'delta': 'azul'}},
                {'method': 'turn/completed', 'params': {
                    'threadId': 'h', 'turn': {'id': 't', 'status': 'completed'}}},
            ]
            self.assertEqual(await server.finish('h', 't'), ('completed', 'azul', []))
            server.events = [{'method': 'turn/completed', 'params': {
                'threadId': 'h', 'turn': {'id': 't', 'status': 'failed',
                                       'error': {'codexErrorInfo': 'usageLimitExceeded'}}}}]
            with self.assertRaisesRegex(SmokeError, 'límite de uso'):
                await server.finish('h', 't')
        asyncio.run(check())

    def test_cancel_wait_preserves_buffered_events(self):
        async def check():
            server = Server('/tmp')
            delta = {'method': 'item/agentMessage/delta', 'params': {
                'threadId': 'h', 'turnId': 't', 'delta': 'partial'}}
            complete = {'method': 'turn/completed', 'params': {
                'threadId': 'h', 'turn': {'id': 't', 'status': 'interrupted'}}}
            server.events = [delta, complete]
            await server.wait_for_delta('h', 't')
            self.assertEqual(await server.finish('h', 't'), ('interrupted', 'partial', []))
            server.events = [complete]
            with self.assertRaises(SmokeError):
                await server.wait_for_delta('h', 't')
        asyncio.run(check())

    def test_tool_requests_are_never_approved(self):
        async def check():
            server = Server('/tmp')
            replies = []
            async def send(message):
                replies.append(message)
            server.send = send
            reader = asyncio.StreamReader()
            class Process:
                stdout = reader
            server.process = Process()
            for method in ('item/commandExecution/requestApproval',
                           'item/fileChange/requestApproval', 'unknown/request'):
                reader.feed_data((json.dumps({'id': 7, 'method': method}) + '\n').encode())
                await server.read()
            self.assertEqual(replies[0]['result']['decision'], 'decline')
            self.assertEqual(replies[1]['result']['decision'], 'decline')
            self.assertIn('error', replies[2])
            reader.feed_eof()
            with self.assertRaises(SmokeError):
                await server.read()
        asyncio.run(check())


if __name__ == '__main__':
    unittest.main()
