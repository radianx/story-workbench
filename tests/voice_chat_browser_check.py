"""Voz → chat editorial persistente → lector. Proveedores y micrófono simulados."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from test_desktop_features import MODELS
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-voice-chat-') as directory:
    server=AppServer(0,directory);server.account.set(status='connected',models=MODELS)
    project=server.store.create('Chat oral ficticio',True)['id'];release=threading.Event();connections=[]
    def connect(data,consent,actions,relay=False):
        assert relay and consent;connections.append(data['id'])
        return dict(token='fixture',model='gemini-3.1-flash-live-preview',setup={'model':'fixture'})
    server.realtime.connect_gemini=connect
    server.realtime.read_session=lambda provider,consent:dict(token='reader',setup={},model='fixture')
    def worker(project,run,docs):
        release.wait(20);server.assistant.update(project,run['id'],status='completed',text='¿Qué pierde la protagonista si decide volver?')
        server.assistant.active=None
    server.assistant.worker=worker
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required'])
            page=browser.new_page(permissions=['microphone']);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script('''
localStorage.setItem('sw-setup-seen','1');window.sockets=[];window.readTexts=[];
const originalFetch=window.fetch;window.ttsDone=false;
window.fetch=(url,options)=>{
 if(String(url)!=='/api/realtime/speech')return originalFetch(url,options);
 const body=JSON.parse(options.body);let value={parts:[],done:false};
 if(body.action==='start'){readTexts.push(body.text);ttsDone=false;value={id:'fixture'};}
 if(body.action==='cancel')value={cancelled:true};
 if(body.action==='poll'&&ttsDone){const pcm=new Int16Array(2400);pcm.fill(1000);value={done:true,parts:[{mimeType:'audio/pcm;rate=24000',data:btoa(String.fromCharCode(...new Uint8Array(pcm.buffer)))}]};}
 return Promise.resolve(new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}}));
};

window.WebSocket=class {
 static OPEN=1;readyState=1;bufferedAmount=0;
 constructor(url){sockets.push(this);setTimeout(()=>this.onopen?.(),0);}
 emit(data){this.onmessage?.({data:JSON.stringify(data)});}
 send(raw){const data=JSON.parse(raw);if(data.setup)this.emit({setupComplete:{}});
  if(data.realtimeInput?.text){readTexts.push(data.realtimeInput.text);window.readerSocket=this;}}
 close(){this.readyState=3;}
};
''')
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.locator('#settings-open').click();page.locator('#realtime-enabled').check()
            assert page.locator('#voice-mode').input_value()=='chat'
            page.locator('#realtime-provider').select_option('gemini');page.locator('#realtime-key').fill('AQ.fixture-voice-chat')
            page.locator('#realtime-consent').check();page.locator('#realtime-save').click();page.locator('#dictate').click()
            page.wait_for_function('()=>realtime?.ready');assert page.locator('#auto-read').is_checked()
            def receive(content):
                page.evaluate('(content)=>sockets[0].emit({serverContent:content})',content)
                if content.get('inputTranscription',{}).get('finished'):page.evaluate('()=>sockets[0].emit({serverContent:{turnComplete:true}})')
            receive({'inputTranscription':{'text':'Mi protagonista '}})
            receive({'turnComplete':True}) # La transcripción puede llegar después del cierre.
            receive({'inputTranscription':{'text':'quiere volver a casa.'}})
            page.wait_for_function('()=>realtime?.relayRun')
            runs=server.store.load(project)['runs'];assert len(runs)==1 and runs[0]['prompt']=='Mi protagonista quiere volver a casa.'
            assert page.locator('#prompt').input_value()==''
            assert page.evaluate('realtime.waiting && !realtime.stream.getAudioTracks()[0].enabled')
            receive({'turnComplete':True});page.wait_for_timeout(700);assert len(server.store.load(project)['runs'])==1
            # Respuestas/herramientas propias del proveedor no llegan al usuario ni a la app.
            receive({'modelTurn':{'parts':[{'inlineData':{'mimeType':'audio/pcm;rate=24000','data':'AAAAAA=='}}]}})
            page.evaluate('()=>sockets[0].emit({toolCall:{functionCalls:[{id:"ignored",name:"workbench_action",args:{action:"set_theme",target:"dark",text:"",mode:""}}]}})')
            assert page.evaluate('realtime.output.size===0 && realtime.seen.size===0')
            release.set();page.wait_for_function('()=>readTexts.length===1')
            assert page.evaluate('readTexts')==['¿Qué pierde la protagonista si decide volver?']
            assert page.evaluate('realtime.speaking && !realtime.stream.getAudioTracks()[0].enabled')
            # Detener la lectura conserva la conexión y recupera el toggle continuo.
            page.locator('#read-stop').click();assert page.evaluate('realtime.ready && realtime.stream.getAudioTracks()[0].enabled')
            assert connections==[project]
            # El final natural de una lectura también recupera la escucha continua.
            page.evaluate("()=>{readText('Respuesta ficticia para terminar de leer.').catch(e=>{throw e;});}")
            page.wait_for_function('()=>readTexts.length===2')
            page.evaluate('()=>ttsDone=true')
            page.wait_for_function('()=>!readingActive && realtime.stream.getAudioTracks()[0].enabled')
            # Un borrador escrito se conserva y no se envía automáticamente.
            page.locator('#prompt').fill('Borrador previo.')
            receive({'inputTranscription':{'text':'Una corrección oral.','finished':True}})
            page.wait_for_function('()=>document.querySelector("#prompt").value.includes("Una corrección oral.")')
            assert page.locator('#prompt').input_value()=='Borrador previo.\nUna corrección oral.'
            assert len(server.store.load(project)['runs'])==1 and page.evaluate('!realtime.listening')
            page.locator('#prompt').fill('');page.evaluate('()=>{realtime.actions=false;setVoiceListening(true,true);}')
            receive({'inputTranscription':{'text':'Sin permiso de envío.','finished':True}})
            page.wait_for_function('()=>document.querySelector("#prompt").value.includes("Sin permiso")')
            assert len(server.store.load(project)['runs'])==1
            # OpenAI usa el mismo puente y deduplica por item_id.
            page.locator('#prompt').fill('');page.evaluate('()=>{realtime.provider="openai";realtimeEvent(realtime,{data:JSON.stringify({type:"conversation.item.input_audio_transcription.completed",item_id:"one",transcript:"Texto OpenAI."})});}')
            page.wait_for_function('()=>document.querySelector("#prompt").value==="Texto OpenAI."')
            page.evaluate('()=>realtimeEvent(realtime,{data:JSON.stringify({type:"conversation.item.input_audio_transcription.completed",item_id:"one",transcript:"Texto OpenAI."})})')
            assert page.locator('#prompt').input_value()=='Texto OpenAI.'
            page.evaluate('()=>{realtime.provider="gemini";voiceTranscript(realtime,"No enviar después de cerrar",true);stopRealtime();}')
            page.wait_for_timeout(700);assert page.locator('#prompt').input_value()=='Texto OpenAI.'
            page.evaluate('()=>{window.testSession={relay:true,signature:realtimeSignature(),provider:"gemini",output:new Set()};realtime=testSession;voiceTranscript(realtime,"x".repeat(12001));}')
            assert page.evaluate('realtime===null') and len(page.locator('#prompt').input_value())>12000
            assert not errors,errors
            browser.close()
    finally:release.set();server.shutdown();server.server_close()
print('OK voz del chat: transcripción completa, envío único persistente, lectura del resultado editorial, pausa/reanudación, borrador protegido, permisos, cierre y OpenAI deduplicado.')
