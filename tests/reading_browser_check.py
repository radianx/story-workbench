"""Lectura con proveedores simulados y TTS local; ninguna llamada externa ni micrófono."""
import io,sys,tempfile,threading,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-reading-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out')
    project=server.store.create('Lectura ficticia',True)['id'];sessions=[];local=[]
    def session(provider,consent):
        assert consent is True;sessions.append(provider)
        return dict(token='ephemeral-fixture',model='gpt-realtime',setup={})
    server.realtime.read_session=session
    server.speech.status=lambda:dict(reading=True,dictation=False)
    def synthesize(text):
        local.append(text);output=io.BytesIO()
        with wave.open(output,'wb') as audio:
            audio.setparams((1,2,16000,0,'NONE','not compressed'));audio.writeframes(b'\0\0'*800)
        return output.getvalue()
    server.speech.synthesize=synthesize
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
            page=browser.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.add_init_script('''
              localStorage.setItem('sw-setup-seen','1');window.readerMode='ok';window.readerSent=[];window.readerClosed=0;window.micRequests=0;
              navigator.mediaDevices.getUserMedia=()=>{micRequests++;throw Error('No abrir micrófono');};
              window.WebSocket=class {
                static OPEN=1;readyState=1;
                constructor(url,protocols){this.gemini=url.includes('googleapis');
                  if(!this.gemini&&protocols[1]!=='openai-insecure-api-key.ephemeral-fixture')throw Error('token');
                  setTimeout(()=>{this.onopen?.();if(!this.gemini)this.emit({type:'session.created'});},10);}
                emit(data){if(this.readyState===1)this.onmessage?.({data:this.gemini?new TextEncoder().encode(JSON.stringify(data)).buffer:JSON.stringify(data)});}
                send(raw){const data=JSON.parse(raw);
                  if(data.setup){setTimeout(()=>this.emit({setupComplete:{}}),5);return;}
                  const text=this.gemini?data.realtimeInput.text:data.response.input[0].content[0].text;
                  readerSent.push(text);
                  if(readerMode==='hold')return;
                  if(readerMode==='error'){setTimeout(()=>this.onerror?.(),10);return;}
                  if(readerMode==='tool'){setTimeout(()=>this.emit({toolCall:{functionCalls:[{name:'workbench_action'}]}}),10);return;}
                  setTimeout(()=>{
                    {
                      const samples=new Int16Array(2400);if(readerMode!=='silent')samples.fill(1000);const pcm=readerMode==='empty'?'':btoa(String.fromCharCode(...new Uint8Array(samples.buffer)));
                      this.emit(this.gemini?{serverContent:{modelTurn:{parts:[{inlineData:{mimeType:'audio/pcm;rate=24000',data:pcm}}]}}}:{type:'response.output_audio.delta',delta:pcm});
                    }
                    this.emit(this.gemini?{serverContent:{turnComplete:true}}:{type:'response.done',response:{status:'completed'}});
                  },10);
                }
                close(){if(this.readyState===3)return;this.readyState=3;readerClosed++;this.onclose?.();}
              };
            ''')
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.locator('#settings-open').click()
            page.locator('#voice-volume').evaluate("e=>{e.value='35';e.dispatchEvent(new Event('input'));}")
            page.locator('#voice-volume').focus();page.keyboard.press('ArrowRight')
            assert page.locator('#voice-volume-value').inner_text()=='36%'
            page.locator('#settings-close').click()
            page.evaluate("""()=>{
              window.gains=[];window.localVolumes=[];
              const play=playGeminiAudio;playGeminiAudio=(s,a)=>{const audible=play(s,a);gains.push(s.volumeNode?.gain.value);return audible;};
              const localPlay=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){localVolumes.push(this.volume);return localPlay.call(this);};
            }""")
            page.evaluate("()=>readText('Lectura local inicial.')")
            assert local==['Lectura local inicial.'] and not sessions
            assert page.evaluate('localVolumes')==[.36]
            for provider in ('openai','gemini'):
                page.evaluate("p=>{$('realtime-provider').value=p;realtimeConfigured=true;realtimeConsent=true;$('realtime-enabled').checked=true;readerSent=[];}",provider)
                value=('Una escena ficticia en la biblioteca. '*35).strip()
                page.evaluate('text=>readText(text)',value)
                assert page.evaluate("readerSent.join('')")==value and sessions[-1]==provider
                assert len(local)==1 and page.evaluate('!readingActive && onlineReading===null && micRequests===0')
            assert all(abs(gain-.36)<.00001 for gain in page.evaluate('gains'))
            for failure in ('error','empty','silent','tool','hold'):
                page.evaluate('mode=>readerMode=mode',failure)
                value='Respaldo local por '+failure
                page.evaluate('text=>readText(text)',value)
                assert local[-1]==value
                assert 'respaldo' in page.locator('#voice-status').inner_text()
                if failure in ('empty','silent','hold'):assert 'No llegó audio' in page.locator('#voice-status').inner_text()
            before=len(local)
            page.evaluate("()=>{readerMode='hold';window.readingPromise=readText('Lectura cancelada.');}")
            page.wait_for_function('()=>onlineReading?.pending')
            page.locator('#read-stop').click();page.evaluate('()=>readingPromise')
            assert len(local)==before and page.evaluate('!readingActive && onlineReading===null')
            # La cancelación también libera una activación de audio suspendida por el motor.
            count=len(sessions)
            page.evaluate("()=>{window.originalResume=AudioContext.prototype.resume;AudioContext.prototype.resume=()=>new Promise(()=>{});window.readingPromise=readText('Audio bloqueado.');}")
            page.locator('#read-stop').click();page.evaluate('()=>readingPromise')
            assert len(sessions)==count and len(local)==before
            page.evaluate('()=>{AudioContext.prototype.resume=originalResume;}')
            # Cancelar mientras llega el token no abre luego un socket ni activa el respaldo.
            pending=[]
            page.route('**/api/realtime/read-session',lambda route:pending.append(route))
            sockets=page.evaluate('readerClosed');before=len(local)
            page.evaluate("()=>{window.readingPromise=readText('Token cancelado.');}")
            page.wait_for_timeout(100);assert pending
            page.locator('#read-stop').click()
            pending[0].fulfill(status=200,content_type='application/json',body='{"token":"ephemeral-fixture","model":"gpt-realtime","setup":{}}')
            page.evaluate('()=>readingPromise')
            assert page.evaluate('readerClosed')==sockets and len(local)==before
            page.unroute('**/api/realtime/read-session')
            # La casilla visible narra respuestas nuevas incluso con conversación oral activa.
            page.locator('.composer-bottom #auto-read').check()
            page.evaluate("""()=>{
              readerMode='hold';readerSent=[];window.stoppedMic=false;
              realtime={provider:'gemini',output:new Set(),stream:{getTracks:()=>[{stop:()=>stoppedMic=true}]}};
              recording={};
              state.runs.push({id:'auto-fixture',status:'completed',text:'Una nueva respuesta editorial.'});
              updateVoice();
            }""")
            assert page.evaluate('!readingActive && !stoppedMic && readerSent.length===0')
            page.evaluate('()=>{recording=null;updateVoice();updateVoice();}')
            page.wait_for_function('()=>onlineReading?.pending')
            assert sessions[-1]=='gemini' and page.evaluate('stoppedMic && realtime===null && micRequests===0')
            assert page.evaluate('readerSent')==['Una nueva respuesta editorial.']
            page.locator('#auto-read').uncheck();page.wait_for_function('()=>!readingActive && onlineReading===null')
            count=len(sessions)
            page.evaluate("()=>{state.runs.push({id:'silent-fixture',status:'completed',text:'Respuesta silenciosa.'});updateVoice();}")
            page.locator('#auto-read').check();page.evaluate('updateVoice()');page.wait_for_timeout(200)
            assert len(sessions)==count and len(local)==before
            page.locator('#auto-read').uncheck()
            page.screenshot(path='/tmp/story-workbench-reading-checkbox.png')
            # Preferencia local persistida: aunque el proveedor esté autorizado no crea sesión.
            count=len(sessions)
            page.evaluate("()=>{$('reading-mode').value='local';$('reading-mode').onchange();}")
            page.evaluate("()=>readText('Solo voz local elegida.')")
            assert len(sessions)==count and local[-1]=='Solo voz local elegida.'
            page.reload();page.locator('#workspace').wait_for()
            assert page.locator('#reading-mode').input_value()=='local'
            assert page.locator('#voice-volume').input_value()=='36'
            assert page.evaluate('micRequests')==0
            assert not server.store.load(project)['runs'] and not server.store.load(project)['decisions']
            assert not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK lectura: OpenAI/Gemini simulados, sin micrófono, fragmentos completos, TTS de respaldo, cancelación, sin herramientas y preferencia persistida.')
