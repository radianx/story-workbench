"""Prueba optativa Linux: emite cuatro tonos y mide SOLO su salida, sin micrófono/red.

Ejecutar con /usr/bin/python3 en una sesión gráfica con WebKitGTK 4.1, GI y parec.
No graba el mezclador general ni guarda audio. No prueba la audición física.
"""
import json, math, os, struct, subprocess, tempfile, threading, time
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, WebKit2, GLib

name='sw-pcm-check-'+str(os.getpid())
GLib.set_prgname(name)
sink=subprocess.check_output(['pactl','get-default-sink'],text=True).strip()
threads=[];ends={};results=[];errors=[]

def capture(label):
    try:
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            streams=json.loads(subprocess.check_output(['pactl','-f','json','list','sink-inputs'],text=True))
            streams=[s for s in streams if s.get('properties',{}).get('application.name')==name and s['sample_specification']=='s16le 1ch 24000Hz']
            if streams:break
            time.sleep(.01)
        assert len(streams)==1, 'No se identificó la salida WAV de la prueba.'
        stream=streams[0];assert stream['sink']>=0
        with tempfile.TemporaryFile() as output:
            process=subprocess.Popen(['parec',f'--monitor-stream={stream["index"]}',f'--device={sink}.monitor','--format=s16le','--rate=24000','--channels=2','--latency-msec=50'],stdout=output,stderr=subprocess.PIPE)
            try:assert ends[label].wait(8), 'Reproductor atascado.'
            finally:process.terminate();process.communicate(timeout=3)
            output.seek(0);samples=[v[0] for v in struct.iter_unpack('<h',output.read())][::2]
        levels=[math.sqrt(sum(v*v for v in samples[i:i+1200])/len(samples[i:i+1200])) for i in range(0,len(samples),1200)]
        audible=[i for i,v in enumerate(levels) if v>300]
        assert 2.9<=len(audible)*.05<=3.1, 'Tono ausente o incompleto.'
        core=levels[audible[0]+1:audible[-1]]
        assert core and all(2050<v<2200 for v in core), 'Señal entrecortada o alterada.'
        results.append(label);print(f'OK {label}: tono completo, nivel estable, salida {sink}.',flush=True)
    except Exception as error:errors.append(f'{label}: {error}')

manager=WebKit2.UserContentManager();manager.register_script_message_handler('probe')
def report(_,result):
    value=json.loads(result.get_js_value().to_string())
    if 'case' in value:
        label=value['case'];ends[label]=threading.Event()
        thread=threading.Thread(target=capture,args=(label,));threads.append(thread);thread.start()
    if 'end' in value:ends[value['end']].set()
    if 'error' in value:errors.append(value['error'])
    if value.get('done'):Gtk.main_quit()
manager.connect('script-message-received::probe',report)
web=WebKit2.WebView(user_content_manager=manager,website_policies=WebKit2.WebsitePolicies(autoplay=WebKit2.AutoplayPolicy.ALLOW))
window=Gtk.Window(title='Story Workbench: comprobación de salida de audio');window.set_default_size(540,140);window.add(web)
script=(Path(__file__).resolve().parents[1]/'web/gemini-voice.js').read_text()
driver='''
const wait=ms=>new Promise(r=>setTimeout(r,ms)),log=x=>window.webkit.messageHandlers.probe.postMessage(JSON.stringify(x));
(async()=>{
 if(!bufferedVoicePlayback)throw Error('Esta prueba requiere WebKitGTK Linux.');
 const bytes=new Uint8Array(24000*2*4),view=new DataView(bytes.buffer);
 for(let i=12000;i<84000;i++)view.setInt16(i*2,Math.sin(i*2*Math.PI*440/24000)*3000,true);
 let raw='';for(let i=0;i<bytes.length;i+=4096)raw+=String.fromCharCode(...bytes.subarray(i,i+4096));
 for(let i=0;i<4;i++){
  const session={output:new Set()},label='WAV-'+i+(i%2?' con reloj de entrada':'');
  if(i%2){session.audioContext=new AudioContext({sampleRate:16000});await session.audioContext.resume();}
  session.onPlaybackError=e=>log({error:e.message});
  playGeminiAudio(session,{mimeType:'audio/pcm;rate=24000',data:btoa(raw)});
  log({case:label});flushGeminiAudio(session);
  while(session.output.size)await wait(20);
  log({end:label});clearGeminiAudio(session);await session.audioContext?.close();await wait(500);
 }
 log({done:true});
})().catch(e=>{log({error:e.message});log({done:true});});
'''
web.load_html('<p>Cuatro tonos locales de tres segundos. No se abre el micrófono.</p><script>let voiceVolume=1;'+script+driver+'</script>','http://localhost/')
window.show_all();GLib.timeout_add_seconds(30,lambda:(errors.append('Tiempo agotado.'),Gtk.main_quit(),False)[-1]);Gtk.main()
for thread in threads:thread.join()
window.destroy()
assert len(results)==4 and not errors,errors
