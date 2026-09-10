import base64
import io
import json
import tempfile
import unittest
import zipfile
from src.workbench_export import export_project
from unittest.mock import patch
from PIL import Image
from src.workbench_images import Images
from src.workbench_store import Store, Problem


def png():
    out=io.BytesIO(); Image.new('RGB',(8,12),'purple').save(out,format='PNG');return out.getvalue()


class ImagesTest(unittest.TestCase):
    def test_providers_bytes_approval_cancel_and_secrets(self):
        for provider in ('openai','gemini'):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as directory:
                store=Store(directory);project=store.create('Imagen ficticia')['id'];manager=Images(lambda p:'test-secret')
                with self.assertRaises(Problem):manager.start(project,dict(provider=provider,prompt='Paisaje',consent=False))
                raw=png();encoded=base64.b64encode(raw).decode()
                response={'data':[{'b64_json':encoded}]} if provider=='openai' else {'candidates':[{'content':{'parts':[{'inlineData':{'data':encoded}}]}}]}
                with patch('src.workbench_images.threading.Thread'):
                    job=manager.start(project,dict(provider=provider,prompt='Paisaje',consent=True))
                self.assertNotIn('test-secret',str(job))
                with patch('src.workbench_images.urllib.request.build_opener') as opener:
                    opener.return_value.open.return_value.__enter__.return_value.read.return_value=json.dumps(response).encode()
                    manager.generate(manager.job,'test-secret')
                    request=opener.return_value.open.call_args.args[0]
                    self.assertTrue(request.full_url.startswith('https://'))
                    self.assertNotIn(project,request.data.decode())
                self.assertEqual(manager.job['status'],'ready')
                self.assertFalse(store.load(project).get('images'))
                with self.assertRaises(Problem):manager.snapshot(job['id'],'wrong-project')
                record=manager.save(store,project,job['id'])
                self.assertEqual(store.path(project,'images',record['file']).read_bytes(),raw)
                self.assertEqual(record,manager.save(store,project,job['id']))
                self.assertEqual(len(store.load(project)['images']),1)
                exported,mime=export_project(store,project)
                with zipfile.ZipFile(io.BytesIO(exported)) as bundle:
                    self.assertEqual(bundle.read('images/'+record['file']),raw)
                    self.assertNotIn('runs',json.loads(bundle.read('manifest.json')))
                self.assertEqual(mime,'application/zip')
                self.assertFalse(store.load(project).get('production'))
                self.assertNotIn('test-secret',store.path(project,'project.json').read_text())
                manager.cancel(job['id'],project)
                self.assertNotIn('data',manager.job)

    def test_bad_response_and_cancel_in_flight(self):
        manager=Images(lambda p:'test-secret')
        with patch('src.workbench_images.threading.Thread'):
            manager.start('project',dict(provider='gemini',prompt='Luna',consent=True))
        manager.cancel(manager.job['id'],'project')
        with patch('src.workbench_images.urllib.request.build_opener',side_effect=RuntimeError('test-secret')):
            manager.generate(manager.job,'test-secret')
        self.assertEqual(manager.job['status'],'cancelled')
        manager.job['status']='generating'
        with patch('src.workbench_images.urllib.request.build_opener',side_effect=RuntimeError('test-secret')):
            manager.generate(manager.job,'test-secret')
        self.assertEqual(manager.job['status'],'failed')
        self.assertNotIn('test-secret',str(manager.job))
