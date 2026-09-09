"""Micrófono virtual de Chromium y respuestas de voz simuladas; nunca captura audio del usuario."""
import io
from pathlib import Path
import sys
import tempfile
import threading
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from workbench_voice import decode_pcm
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-voice-browser-') as temp:
    server=AppServer(0,temp);server.account.set(status='signed_out')
    project=server.store.create('Voz ficticia',True)['id']
    server.speech.status=lambda:dict(dictation=True,reading=True,local=True,max_seconds=45)
    transcriptions=[];reads=[]
    def transcribe(encoded):
        pcm=decode_pcm(encoded);assert len(pcm)>0;transcriptions.append(pcm)
        return {'text':'Una biblioteca ficticia en el mar','local':True}
    server.speech.transcribe=transcribe
    def synthesize(text):
        reads.append(text);audio=io.BytesIO()
        with wave.open(audio,'wb') as w:w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*1600)
        return audio.getvalue()
    server.speech.synthesize=synthesize
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--use-fake-device-for-media-stream'])
            page=browser.new_page(permissions=['microphone']);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token)
            page.locator('#dictate:not([disabled])').wait_for()
            page.locator('#prompt').fill('Mi idea:')
            page.locator('#dictate').click()
            page.wait_for_function("() => document.querySelector('#voice-status').textContent.includes('Grabando')")
            assert page.locator('#send').is_disabled()
            page.wait_for_timeout(400);page.locator('#dictate').click()
            page.wait_for_function("() => document.querySelector('#prompt').value.includes('Una biblioteca ficticia')")
            assert len(transcriptions)==1 and server.store.load(project)['runs']==[]
            assert page.locator('#prompt').input_value().startswith('Mi idea:')
            assert page.evaluate('recording===null && !transcribing')
            page.locator('#dictate').click();page.wait_for_function("() => document.querySelector('#voice-status').textContent.includes('Grabando')")
            page.locator('#dictate-cancel').click();page.get_by_text('Dictado descartado.',exact=True).wait_for()
            assert len(transcriptions)==1
            # Mantener Espacio dicta sin enviar; soltar transcribe y devuelve el teclado.
            page.locator('#prompt').fill('');page.keyboard.down('Space');page.wait_for_function('()=>!!recording?.node')
            page.wait_for_timeout(400);page.keyboard.down('Space');assert page.locator('#prompt').input_value()=='';page.keyboard.up('Space');page.wait_for_function('()=>!recording&&!transcribing')
            assert len(transcriptions)==2 and server.store.load(project)['runs']==[], (len(transcriptions),page.locator('#voice-status').inner_text(),page.evaluate('({spaceListening,recording,transcribing})'))
            page.locator('#prompt').focus();page.keyboard.press('Space');assert page.evaluate('recording===null')
            # Error de permiso controlado: vuelve a permitir entrada escrita.
            page.evaluate("() => {navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('denied','NotAllowedError')}}")
            page.locator('#dictate').click();page.get_by_text('Micrófono no autorizado. Podés responder escribiendo.',exact=True).wait_for()
            assert page.locator('#send').is_enabled()
            with server.store.lock:
                data=server.store.load(project);data['runs']=[dict(id='voice-test',mode='interview',prompt='Prueba',status='completed',text='¿Qué querés que sienta el lector?',sources=[],date=0)];server.store.persist(data)
            page.locator('#settings-open').click();page.locator('#read-last:not([disabled])').wait_for()
            page.locator('#read-last').click();page.locator('#settings-close').click();page.get_by_text('Lectura terminada.',exact=True).wait_for()
            assert reads==['¿Qué querés que sienta el lector?']
            assert page.evaluate('readingAudio===null && readingURL===null')
            page.locator('[data-read=voice-test]').click();page.get_by_text('Lectura terminada.',exact=True).wait_for()
            assert reads==['¿Qué querés que sienta el lector?']*2
            # Lectura automática solo al elegirla, y solo una vez por respuesta nueva.
            page.locator('.composer-bottom #auto-read').check()
            with server.store.lock:
                data=server.store.load(project);data['runs'].append({**data['runs'][0],'id':'voice-test2','text':'¿Quién es la protagonista?'});server.store.persist(data)
            page.wait_for_function("() => document.querySelectorAll('.run').length===2")
            page.get_by_text('Lectura terminada.',exact=True).wait_for();page.wait_for_timeout(1800)
            assert reads==['¿Qué querés que sienta el lector?']*2+['¿Quién es la protagonista?']
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close()
print('OK voz en navegador: micrófono virtual, PCM, transcripción revisable sin envío, descarte, permiso denegado, lectura y lectura automática única.')
