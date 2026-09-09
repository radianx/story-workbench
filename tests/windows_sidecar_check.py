"""Windows sidecar handshake, HTTP and stdin shutdown, natively or under Wine."""
import argparse,json,os,subprocess,tempfile,urllib.request,queue,threading
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--wine',action='store_true')
parser.add_argument('--runtime',type=Path,default=ROOT/'src-tauri/runtime')
parser.add_argument('--binary',type=Path,default=ROOT/'src-tauri/binaries/story-server-x86_64-pc-windows-msvc.exe')
args=parser.parse_args()
def native(path):
    value=str(path.resolve())
    return 'Z:'+value.replace('/','\\') if args.wine else value
if args.wine:assert os.environ.get('WINEPREFIX','').startswith('/tmp/'), 'Use an isolated Wine prefix.'
runtime=args.runtime.resolve()
assert json.loads((runtime/'MANIFEST.json').read_text())['target']=='win'
with tempfile.TemporaryDirectory(prefix='sw-windows-sidecar-') as directory:
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','STORY_DESKTOP':'1','STORY_SERVER_RUNTIME':native(runtime),
         'STORY_CODEX_BINARY':native(runtime/'codex/bin/codex.exe'),'STORY_VOICE_DIR':native(runtime/'voice'),
         'CODEX_HOME':native(Path(directory)/'codex')}
    for _ in range(2):
        command=(['wine',str(args.binary.resolve())] if args.wine else [str(args.binary.resolve())])+['--port','0','--data-dir',native(Path(directory)/'projects')]
        process=subprocess.Popen(command,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        lines=queue.Queue()
        def receive(pipe=process.stdout,destination=lines):
            for line in pipe:destination.put(line)
            destination.put(None)
        reader=threading.Thread(target=receive,daemon=True);reader.start()
        try:
            backend=None
            for _ in range(20):
                line=lines.get(timeout=30)
                if line is None:
                    print(process.stderr.read().decode('utf-8',errors='replace')[-2000:])
                    raise AssertionError('Sidecar exited before handshake')
                try:value=json.loads(line)
                except ValueError:continue
                if isinstance(value,dict) and 'origin' in value and 'token' in value:backend=value;break
            assert backend, 'No handshake'
            request=urllib.request.Request(backend['origin']+'/api/projects',headers={'Authorization':'Bearer '+backend['token']})
            with urllib.request.urlopen(request,timeout=10) as response:assert response.status==200
            process.stdin.close();assert process.wait(timeout=30)==0
            try:urllib.request.urlopen(request,timeout=2)
            except OSError:pass
            else:raise AssertionError('Python still listening after launcher shutdown')
        finally:
            if process.poll() is None:process.stdin.close();process.wait(timeout=30)
print('OK sidecar Windows: handshake, HTTP y cierre por stdin; segundo arranque sin lock retenido.')
