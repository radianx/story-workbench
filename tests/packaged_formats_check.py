"""Run the extracted Linux backend with a disposable profile and no provider calls."""
import argparse
import base64
import json
from pathlib import Path
import os
import queue
import subprocess
import tempfile
import threading
import urllib.request

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary',type=Path,required=True)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='sw-packaged-') as directory:
    env={**os.environ,'STORY_DESKTOP':'1','CODEX_HOME':directory+'/codex'}
    process=subprocess.Popen([str(args.binary.resolve()),'--port','0','--data-dir',directory+'/projects'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    lines=queue.Queue()
    def read():
        for line in process.stdout:lines.put(line)
        lines.put(None)
    threading.Thread(target=read,daemon=True).start()
    try:
        backend=json.loads(lines.get(timeout=30));origin=backend['origin']
        headers={'Authorization':'Bearer '+backend['token'],'Content-Type':'application/json','Origin':origin}
        def request(path,body=None):
            req=urllib.request.Request(origin+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
            with urllib.request.urlopen(req,timeout=20) as response:
                raw=response.read()
                return json.loads(raw) if 'application/json' in response.headers['Content-Type'] else raw
        for name in ('app.js','bootstrap.js','images.js','formats.js'):
            assert request('/'+name)==(ROOT/'web'/name).read_bytes(),name
        project=request('/api/projects',{'title':'Edición ficticia','documents':[{'name':'Capítulo','role':'manuscrito','content':'El río conservó su voz.'}]})['id']
        pdf=request('/api/projects/'+project+'/book.pdf');assert pdf.startswith(b'%PDF-')
        docx=request('/api/projects/'+project+'/book.docx')
        imported=request('/api/import/file',{'name':'Edición.docx','data':base64.b64encode(docx).decode()})
        assert 'El río conservó su voz.' in imported['documents'][0]['content']
        assert request('/api/images/providers')=={'openai':False,'gemini':False}
        process.stdin.close();assert process.wait(timeout=30)==0
        print('OK extracted Linux backend: current web modules, persisted project, PDF/fonts and DOCX import; no AI calls.')
    finally:
        if process.poll() is None:
            process.stdin.close();process.wait(timeout=30)
