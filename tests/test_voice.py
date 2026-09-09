import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
import wave
from unittest.mock import patch
from workbench_voice import Speech, decode_pcm, RATE, MAX_SECONDS
from workbench_store import Problem
import test_workbench


class Voice(unittest.TestCase):
    def test_audio_limits_and_synthesis_without_shell_interpolation(self):
        self.assertEqual(decode_pcm(base64.b64encode(b'\0\0').decode()),b'\0\0')
        for value in ('','no base64',base64.b64encode(b'1').decode(),base64.b64encode(b'\0'*(RATE*MAX_SECONDS*2+2)).decode(),None):
            with self.assertRaises(Problem):decode_pcm(value)
        output=io.BytesIO()
        with wave.open(output,'wb') as w:w.setparams((1,2,22050,0,'NONE','not compressed'));w.writeframes(b'\0\0'*500)
        speech=Speech();speech.tts='/fixed/espeak-ng'
        text='Hola `comando` $(no ejecutar) & <texto>'
        with patch('workbench_voice.subprocess.run') as run:
            run.return_value.returncode=0;run.return_value.stdout=output.getvalue()
            result=speech.synthesize(text)
            self.assertEqual(run.call_args.kwargs['input'],text.encode())
            self.assertNotIn(text,run.call_args.args[0])
            self.assertNotIn('shell',run.call_args.kwargs)
            with wave.open(io.BytesIO(result)) as w:self.assertEqual(w.getnframes(),500)
        with self.assertRaises(Problem):speech.synthesize('x'*2001)
        speech.tts=None
        with self.assertRaises(Problem):speech.synthesize('Hola')
        with tempfile.TemporaryDirectory() as temp:
            speech.library=Path(temp)/'missing';speech.model_path=Path(temp)/'missing'
            self.assertFalse(speech.status()['dictation'])
            with self.assertRaises(Problem):speech.transcribe('AAA=')
            self.assertFalse(speech.lock.locked())


class VoiceHTTP(unittest.TestCase):
    setUp=test_workbench.HTTPTests.setUp
    request=test_workbench.HTTPTests.request

    def test_voice_endpoints_remain_authenticated_and_do_not_create_projects(self):
        for path in ('/api/voice/transcribe','/api/voice/read'):
            self.assertEqual(self.request(path,{'text':'Hola','pcm':'AAA='},headers={'Authorization':'no'})[0],401)
        status,body=self.request('/api/voice');self.assertEqual(status,200)
        self.assertTrue(json.loads(body)['local'])
        with patch.object(self.server.speech,'transcribe',return_value={'text':'Una biblioteca','local':True}):
            status,body=self.request('/api/voice/transcribe',{'pcm':'AAA='})
            self.assertEqual(status,200);self.assertEqual(json.loads(body)['text'],'Una biblioteca')
        self.assertEqual(self.server.store.list_projects(),[])
