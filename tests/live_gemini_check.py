"""Opt-in con clave por stdin: voz sintética temporal, una conexión Gemini de hasta 40 s."""
import json
import base64
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright

if sys.stdin.isatty():
    import termios
    terminal=termios.tcgetattr(sys.stdin);quiet=terminal.copy();quiet[3]&=~termios.ECHO;termios.tcsetattr(sys.stdin,termios.TCSANOW,quiet)
    print('Esperando clave por entrada privada.',flush=True)
key=sys.stdin.readline().strip()
if sys.stdin.isatty():termios.tcsetattr(sys.stdin,termios.TCSANOW,terminal)
assert key,'Falta la clave por stdin'
with tempfile.TemporaryDirectory(prefix='sw-live-gemini-') as directory:
    wav=Path(directory)/'synthetic.wav'
    subprocess.run(['espeak-ng','-v','es','-s','145','-w',str(wav),'Hola. Cambia el tema a oscuro y dime una frase sobre un puerto flotante imaginario.'],check=True)
    server=AppServer(0,directory);server.account.set(status='signed_out')
    server.store.create('Puerto ficticio de prueba',True)
    server.realtime.configure(key,'gemini');key=''
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required'])
            page=browser.new_page(permissions=['microphone'])
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.evaluate("""async encoded=>{window.testAudio=new AudioContext({sampleRate:16000});const buffer=await testAudio.decodeAudioData(Uint8Array.from(atob(encoded),c=>c.charCodeAt(0)).buffer);window.testSpeech=testAudio.createBufferSource();testSpeech.buffer=buffer;const dest=testAudio.createMediaStreamDestination();testSpeech.connect(dest);navigator.mediaDevices.getUserMedia=async()=>dest.stream;window.receivedAudio=0;window.voiceFrames=0;window.nonzeroFrames=0;const send=sendGemini;sendGemini=(s,m)=>{if(m.realtimeInput?.audio){voiceFrames++;if(atob(m.realtimeInput.audio.data).split('').some(c=>c.charCodeAt(0)>0))nonzeroFrames++;}return send(s,m)};const play=playGeminiAudio;playGeminiAudio=(s,a)=>{receivedAudio++;return play(s,a)};}""",base64.b64encode(wav.read_bytes()).decode())
            page.evaluate("()=>{applyTheme('light');document.querySelector('#realtime-provider').value='gemini';document.querySelector('#realtime-provider').onchange();document.querySelector('#realtime-enabled').checked=true;realtimeConsent=true;startRealtime()}")
            try:
                page.wait_for_function('()=>realtime?.ready===true',timeout=40000)
            except Exception:
                print('Conexión:',page.locator('#realtime-status').inner_text(),flush=True);raise AssertionError('Gemini no confirmó setup') from None
            print('OK Gemini real: token temporal y setup confirmado.',flush=True)
            page.evaluate('async()=>{await testAudio.resume();testSpeech.start()}')
            page.wait_for_timeout(15000)
            print('Audio sintético:',page.evaluate('()=>({frames:voiceFrames,nonzero:nonzeroFrames,received:receivedAudio,context:testAudio.state,theme:document.documentElement.dataset.theme,status:document.querySelector("#realtime-status").textContent,caption:document.querySelector("#realtime-caption").textContent,actions:document.querySelector("#realtime-actions").textContent})'),flush=True)
            page.wait_for_function('()=>receivedAudio>0 && document.documentElement.dataset.theme==="dark" && document.querySelector("#realtime-caption").textContent.length>10',timeout=25000)
            print('OK voz sintética enviada, acción de tema ejecutada y respuesta de audio con transcripción recibida.',flush=True)
            page.evaluate('stopRealtime()');assert page.evaluate('realtime===null')
            browser.close()
    finally:
        server.realtime.configure('','gemini');server.shutdown();server.server_close()
