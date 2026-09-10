"""Opt-in: clave Gemini por stdin privado, lectura ficticia real, sin guardar audio ni tokens."""
import sys,tempfile,threading,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.app import AppServer
from playwright.sync_api import sync_playwright

if sys.stdin.isatty():
    import termios
    original=termios.tcgetattr(sys.stdin);quiet=original.copy();quiet[3]&=~termios.ECHO
    termios.tcsetattr(sys.stdin,termios.TCSANOW,quiet)
print('Esperando clave por entrada privada.',flush=True)
key=sys.stdin.readline().strip()
if sys.stdin.isatty():termios.tcsetattr(sys.stdin,termios.TCSANOW,original)
assert key,'Falta clave'
with tempfile.TemporaryDirectory(prefix='sw-live-reading-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out')
    server.store.create('Lectura ficticia',True);server.realtime.configure(key,'gemini');key=''
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page();page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.evaluate("""()=>{
              window.readStats={chunks:0,nonzero:0,seconds:0,fallback:0,ended:false};
              const play=playGeminiAudio;playGeminiAudio=(s,a)=>{const pcm=atob(a.data);readStats.chunks++;readStats.seconds+=pcm.length/48000;readStats.nonzero+=Number([...pcm].some(c=>c.charCodeAt(0)>0));return play(s,a);};
              const request=api;api=(path,...args)=>{if(path==='/api/voice/read')readStats.fallback++;return request(path,...args);};
              $('realtime-provider').value='gemini';$('realtime-enabled').checked=true;realtimeConsent=true;realtimeConfigured=true;
              $('read-last').disabled=false;$('read-last').onclick=()=>{readText('La nave azul descansaba junto al faro.').then(()=>readStats.ended=true,()=>readStats.failed=true);};
            }""")
            page.locator('#settings-open').click();page.locator('#read-last').click();page.locator('#settings-close').click()
            for _ in range(12):
                page.wait_for_timeout(5000)
                stats=page.evaluate("({...readStats,active:readingActive,context:onlineReading?.audioContext.state,pending:!!onlineReading?.pending,status:$('voice-status').textContent})")
                print(json.dumps(stats,ensure_ascii=False),flush=True)
                if stats.get('ended') or stats.get('failed'):break
            page.evaluate('stopReading()');browser.close()
            assert stats['ended'] and stats['nonzero']>0 and stats['fallback']==0,'Lectura Gemini no completada sin respaldo'
    finally:
        server.realtime.configure('','gemini');server.shutdown();server.server_close()
print('OK Gemini real: PCM no silencioso recibido y reproducido, sin respaldo local.')
