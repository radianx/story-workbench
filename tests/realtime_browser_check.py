"""WebRTC y funciones simuladas, micrófono virtual; sin conexión a OpenAI ni cargos."""
import json
from pathlib import Path
import sys
import tempfile
import threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from test_desktop_features import MODELS
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-rtc-') as directory:
    server=AppServer(0,directory);server.account.set(status='connected',models=MODELS)
    project=server.store.create('Voz ficticia',True)['id'];connections=[]
    def connect(data,sdp,consent,actions):
        assert consent is True and sdp.startswith('v=0') and server.realtime.status()['configured']
        connections.append(data['id']);return dict(sdp='v=0\r\nanswer',model='gpt-realtime')
    server.realtime.connect=connect
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--use-fake-device-for-media-stream'])
            page=browser.new_page(permissions=['microphone']);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script('''window.sentRTC=[];window.testTracks=[];
              window.RTCPeerConnection=class {
                addTrack(track){window.testTracks.push(track)}
                createDataChannel(){return this.channel=window.testChannel={readyState:'open',send:v=>sentRTC.push(JSON.parse(v)),close(){this.readyState='closed';this.onclose?.()}}}
                async createOffer(){return {type:'offer',sdp:'v=0\\r\\noffer'}}
                async setLocalDescription(){}
                async setRemoteDescription(){this.channel.onopen()}
                close(){this.connectionState='closed';this.onconnectionstatechange?.()}
              };
              window.toolCall=(id,name,args)=>testChannel.onmessage({data:JSON.stringify({type:'response.done',response:{status:'completed',output:[{type:'function_call',call_id:id,name,arguments:JSON.stringify(args)}]}})});
            ''')
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            assert not page.locator('#realtime-enabled').is_checked() and not connections
            page.evaluate("()=>{$('voice-volume').value='45';$('voice-volume').oninput();}")
            page.locator('#settings-open').click();page.locator('#realtime-enabled').check()
            page.locator('#realtime-key').fill('sk-ficticia-solo-test')
            page.locator('#realtime-save').click();page.get_by_text('Confirmá el envío al proveedor y las condiciones de la API antes de habilitarlo.',exact=True).wait_for()
            assert not connections and not server.realtime.status()['configured']
            page.locator('#notice-close').click();page.locator('#realtime-consent').check();page.locator('#realtime-save').click()
            assert page.locator('#realtime-key').input_value()==''
            assert 'sk-ficticia' not in page.evaluate('JSON.stringify([localStorage,sessionStorage])')
            page.locator('#dictate').click();page.wait_for_function("()=>document.querySelector('#realtime-status').textContent.includes('API activa')")
            assert connections==[project] and page.locator('#send').is_enabled()
            assert page.evaluate('realtime.audio.volume')==.45
            page.evaluate("()=>{$('voice-volume').value='0';$('voice-volume').oninput();}")
            assert page.evaluate('realtime.audio.volume')==0
            def call(id,action,target='',mode='',text=''):
                page.evaluate('(x)=>toolCall(x.id,"workbench_action",x.args)',dict(id=id,args=dict(action=action,target=target,mode=mode,text=text)))
                page.wait_for_function('(id)=>sentRTC.some(e=>e.item?.call_id===id)',arg=id)
                return page.evaluate('(id)=>JSON.parse(sentRTC.find(e=>e.item?.call_id===id).item.output)',id)
            assert call('theme','set_theme','dark')=={'theme':'dark'}
            assert page.locator('#theme').input_value()=='dark'
            assert 'error' in call('deny','accept_translation',text='No aprobar por voz')
            assert call('criterion','prepare_decision',text='Un mundo sin monarquía.')['registered'] is False
            assert page.locator('#decision-status').input_value()=='pending'
            assert server.store.load(project)['decisions']==[]
            # Duplicados no repiten efectos ni respuestas.
            count=page.evaluate('sentRTC.length')
            page.evaluate('()=>toolCall("criterion","workbench_action",{action:"prepare_decision",target:"",mode:"",text:"Duplicado"})')
            page.wait_for_timeout(100);assert page.evaluate('sentRTC.length')==count
            assert call('nav','navigate','conversation')=={'visible':'conversation'}
            page.locator('#prompt').fill('Mensaje humano sin enviar.')
            assert 'error' in call('preserve','prepare_task',mode='diagnosis',text='No reemplazar')
            sent=[]
            page.route('**/api/run',lambda route:(sent.append(route.request.post_data_json),route.fulfill(status=200,content_type='application/json',body='{"id":"test-run"}')))
            assert call('run','start_task',mode='diagnosis',text='Revisá contradicciones de las fuentes.')['started']
            assert sent[0]['mode']=='diagnosis' and page.locator('#prompt').input_value()=='Mensaje humano sin enviar.'
            page.locator('#realtime-mute').click();assert page.evaluate('testTracks.every(t=>!t.enabled)')
            page.locator('#realtime-mute').click();assert page.evaluate('testTracks.every(t=>t.enabled)')
            page.locator('#realtime-stop').click();assert page.evaluate('testTracks.every(t=>t.readyState==="ended")')
            assert page.locator('#send').is_enabled()
            # Modo conversación sin acciones, incluso ante una llamada inventada.
            page.locator('#settings-open').click();page.locator('#realtime-settings').click();page.locator('#realtime-allow-actions').uncheck();page.locator('#realtime-close').click();page.locator('#settings-close').click()
            page.locator('#dictate').click();page.wait_for_function('()=>!!realtime?.channel && !document.querySelector("#realtime-status").textContent.includes("Conectando")')
            assert 'error' in call('not-enabled','set_theme','light')
            # Retirar una fuente detiene la sesión y libera el micrófono.
            page.locator('.document-item input[type=checkbox]').first.uncheck()
            page.wait_for_function('()=>realtime===null')
            assert page.evaluate('testTracks.every(t=>t.readyState==="ended")')
            page.locator('#settings-open').click();page.locator('#realtime-settings').click();page.locator('#realtime-forget').click()
            page.wait_for_function('()=>!realtimeConfigured');assert not server.realtime.status()['configured']
            page.locator('#realtime-close').click();page.locator('#settings-close').click()
            # Cancelar mientras el permiso del micrófono todavía se resuelve.
            page.evaluate('()=>{realtimeConfigured=true;realtimeConsent=true;document.querySelector("#realtime-enabled").checked=true;window.originalGetMedia=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getUserMedia=()=>new Promise(resolve=>window.resolveMic=resolve);renderVoice()}')
            page.locator('#dictate').click();page.wait_for_function('()=>!!window.resolveMic');page.locator('#dictate').click()
            assert page.evaluate('realtime.listening===false') and page.locator('#dictate').get_attribute('aria-busy') is None
            page.locator('#realtime-stop').click()
            page.evaluate('async()=>{window.lateStream=await originalGetMedia({audio:true});resolveMic(lateStream)}')
            page.wait_for_function('()=>lateStream.getTracks().every(t=>t.readyState==="ended")')
            assert len(connections)==2 and not errors,errors
            page.screenshot(path='/tmp/story-workbench-realtime.png',full_page=True)
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK Realtime simulado: opt-in, clave sin persistir, acciones, límites editoriales, duplicados, tareas Codex, pausa, cierre y permisos tardíos. Sin API real.')
