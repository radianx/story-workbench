"""Gemini Live simulado con PCM real de micrófono virtual; sin clave real ni red externa."""
import sys
from pathlib import Path
import tempfile
import threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-gemini-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out')
    project=server.store.create('Gemini ficticio',True)['id'];connections=[]
    def connect(data,consent,actions):
        assert consent is True and server.realtime.gemini_key=='AIza-ficticia-solo-test'
        assert not server.realtime.key
        connections.append(data['id']);return dict(token='auth_tokens/solo-test',setup=dict(model='models/gemini-3.1-flash-live-preview'),model='gemini-3.1-flash-live-preview')
    server.realtime.connect_gemini=connect
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--use-fake-device-for-media-stream'])
            page=browser.new_page(permissions=['microphone']);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script('''window.geminiSent=[];window.WebSocket=class {
                static OPEN=1;
                constructor(url){this.url=url;this.readyState=1;this.bufferedAmount=0;window.geminiSocket=this;setTimeout(()=>this.onopen(),0)}
                send(raw){const data=JSON.parse(raw);geminiSent.push(data);if(data.setup)queueMicrotask(()=>this.onmessage({data:JSON.stringify({setupComplete:{}})}))}
                close(){this.readyState=3;this.onclose?.()}
              };
              window.geminiReceive=data=>geminiSocket.onmessage({data:JSON.stringify(data)});
            ''')
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.locator('#realtime-options summary').click();page.locator('#realtime-enabled').check()
            page.locator('#realtime-provider').select_option('gemini')
            assert 'AI Plus' in page.locator('#realtime-provider-note').inner_text()
            page.locator('#realtime-key').fill('AIza-ficticia-solo-test');page.locator('#realtime-consent').check();page.locator('#realtime-save').click()
            page.locator('#realtime-start').click();page.wait_for_function('()=>geminiSent.some(e=>e.realtimeInput?.audio?.data.length>0)')
            assert connections==[project] and not server.realtime.key
            assert page.evaluate('geminiSocket.url.includes("access_token=") && !geminiSocket.url.includes("AIza")')
            assert 'AIza' not in page.evaluate('JSON.stringify([sessionStorage,localStorage])')
            page.evaluate('()=>geminiReceive({toolCall:{functionCalls:[{id:"theme",name:"workbench_action",args:{action:"set_theme",target:"dark",mode:"",text:""}}]}})')
            page.wait_for_function('()=>geminiSent.some(e=>e.toolResponse?.functionResponses[0].id==="theme")')
            assert page.locator('#theme').input_value()=='dark'
            # PCM little-endian 24 kHz reproducible y barge-in sin esperar herramientas.
            page.evaluate('()=>geminiReceive({serverContent:{modelTurn:{parts:[{inlineData:{mimeType:"audio/pcm;rate=24000",data:btoa("\\0".repeat(48000))}}]},outputTranscription:{text:"Una pregunta ficticia."}}})')
            page.wait_for_function('()=>realtime.output.size>0')
            page.evaluate('()=>geminiReceive({serverContent:{interrupted:true}})')
            page.wait_for_function('()=>realtime.output.size===0')
            # Cancelar una acción antes de ejecutarla no cambia la UI.
            page.evaluate('()=>{geminiReceive({toolCallCancellation:{ids:["cancelled"]}});geminiReceive({toolCall:{functionCalls:[{id:"cancelled",name:"workbench_action",args:{action:"set_theme",target:"light",mode:"",text:""}}]}})}')
            page.wait_for_timeout(100);assert page.locator('#theme').input_value()=='dark'
            page.locator('#realtime-mute').click()
            assert page.evaluate('geminiSent.some(e=>e.realtimeInput?.audioStreamEnd)')
            page.evaluate('()=>{window.finishedStream=realtime.stream;window.finishedAudio=realtime.audioContext}')
            page.locator('#realtime-global-stop').click()
            page.wait_for_function('()=>finishedAudio.state==="closed" && finishedStream.getTracks().every(t=>t.readyState==="ended")')
            page.locator('#realtime-settings').click();page.locator('#realtime-provider').select_option('openai')
            assert not page.locator('#realtime-consent').is_checked() and page.locator('#realtime-key').input_value()==''
            assert not page.evaluate('realtimeConfigured') and not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK Gemini simulado: clave propia sin OpenAI, consentimiento, token temporal, PCM entrada/salida, interrupción, acciones, cancelación y cierre.')
