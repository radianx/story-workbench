import asyncio
import tempfile
import unittest
from unittest.mock import patch
from workbench_account import Account, auth_url, list_models, resolve_ai
from workbench_production import validate_production
from workbench_store import Problem


MODELS = [dict(model='modelo-a',displayName='Modelo A',isDefault=True,defaultReasoningEffort='medium',
               supportedReasoningEfforts=[dict(reasoningEffort=e,description=e) for e in ('medium','high')]),
          dict(model='modelo-b',displayName='Modelo B',isDefault=False,defaultReasoningEffort='low',
               supportedReasoningEfforts=[dict(reasoningEffort='low',description='low')])]


class Features(unittest.TestCase):
    def test_models_pagination_and_exact_effort(self):
        class Fake:
            async def rpc(self, method, params):
                assert method=='model/list' and params['includeHidden'] is False
                return {'data': [MODELS[1]],'nextCursor':None} if params['cursor'] else {'data':[MODELS[0],{**MODELS[1],'hidden':True}],'nextCursor':'page2'}
        self.assertEqual(asyncio.run(list_models(Fake())), MODELS)
        self.assertEqual(resolve_ai({},MODELS),{'model':'modelo-a','effort':'medium'})
        self.assertEqual(resolve_ai({'model':'modelo-b'},MODELS),{'model':'modelo-b','effort':'low'})
        for choice in ({'model':'missing'}, {'model':'modelo-b','effort':'high'}, {'effort':'unknown'}, {'model':42}):
            with self.assertRaises(Problem): resolve_ai(choice,MODELS)

    def test_production_validation(self):
        value = dict(width=152.4, height=228.6, spine=20, title='Ficción', author='Autora')
        self.assertEqual(validate_production(value)['spine'], 20)
        for bad in ({'width':True}, {'height':float('nan')}, {'spine':101}, {'front':'https://evil.test/cover'}, {'back':'data:image/jpeg;base64,YWJj'}):
            with self.assertRaises(Problem): validate_production({**value, **bad})

    def test_auth_allowlist(self):
        self.assertEqual(auth_url('https://auth.openai.com/oauth/authorize?state=ficticio'), 'https://auth.openai.com/oauth/authorize?state=ficticio')
        for url in ('http://auth.openai.com','https://auth.openai.com.evil.test','file:///etc/passwd','https://evil@auth.openai.com','https://auth.openai.com:444/a'):
            with self.assertRaises(Problem): auth_url(url)

    def test_account_login_protocol_and_no_secrets(self):
        calls=[]
        class Fake:
            def __init__(self,*_,**__): self.events=[]; self.reads=0
            async def __aenter__(self): return self
            async def __aexit__(self,*_): pass
            async def rpc(self,method,params):
                calls.append((method,params))
                if method=='model/list': return {'data':MODELS,'nextCursor':None}
                if method=='account/read':
                    self.reads+=1
                    return {'account':None if self.reads==1 else {'type':'chatgpt','email':'secret@example.test'}}
                if method=='account/login/start': return {'type':'chatgpt','loginId':'fake-id','authUrl':'https://auth.openai.com/oauth/authorize?state=fake'}
                return {}
            async def read(self): return {'method':'account/login/completed','params':{'loginId':'fake-id','success':True}}
        with tempfile.TemporaryDirectory() as directory, patch('workbench_account.Server',Fake):
            account=Account(directory)
            asyncio.run(account.execute('login'))
            self.assertEqual(account.snapshot(),{'status':'connected','models':MODELS})
            self.assertIn(('account/login/start',{'type':'chatgpt'}),calls)
            asyncio.run(account.execute('logout'))
            self.assertEqual(account.snapshot(),{'status':'signed_out'})


if __name__=='__main__': unittest.main()
