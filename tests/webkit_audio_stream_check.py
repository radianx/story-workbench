"""Prueba optativa WebKitGTK/Pulse: latencia y continuidad con PCM incremental.

Usa una salida virtual temporal propia; no micrófono, API, archivos de audio ni
capturas de otras aplicaciones. Ejecutar con /usr/bin/python3 en Linux gráfico.
"""
import json, math, os, struct, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def browser(pace):
    import gi
    gi.require_version('Gtk','3.0');gi.require_version('WebKit2','4.1')
    from gi.repository import Gtk,WebKit2,GLib
    GLib.set_prgname('sw-stream-check')
    manager=WebKit2.UserContentManager();manager.register_script_message_handler('probe')
    results=[]
    def report(_,value):
        results.append(json.loads(value.get_js_value().to_string()));Gtk.main_quit()
    manager.connect('script-message-received::probe',report)
    web=WebKit2.WebView(user_content_manager=manager,website_policies=WebKit2.WebsitePolicies(autoplay=WebKit2.AutoplayPolicy.ALLOW))
    window=Gtk.Window(title='Story Workbench: prueba de latencia aislada');window.add(web);window.show_all()
    driver='''
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms)),log=value=>window.webkit.messageHandlers.probe.postMessage(JSON.stringify(value));
(async()=>{
 if(!bufferedVoicePlayback)throw Error('Se requiere WebKitGTK Linux.');
 await new Promise(resolve=>window.addEventListener('load',resolve,{once:true}));await wait(200);
 const s={output:new Set()},start=performance.now();let first=null,failure=null;
 s.onPlaybackError=error=>{failure=error.message;};
 s.onAudio=()=>{if(s.audio&&!s.audio.paused&&first===null)s.audio.addEventListener('playing',()=>{if(first===null)first=performance.now()-start;},{once:true});};
 for(let n=0;n<60;n++){
  const bytes=new Uint8Array(4800),view=new DataView(bytes.buffer);
  for(let i=0;i<2400;i++)view.setInt16(i*2,Math.sin((n*2400+i)*2*Math.PI*440/24000)*3000,true);
  playGeminiAudio(s,{mimeType:'audio/pcm;rate=24000',data:btoa(String.fromCharCode(...bytes))});await wait(PACE);
 }
 const generated=performance.now()-start;flushGeminiAudio(s);while(s.output.size)await wait(20);
 clearGeminiAudio(s);await wait(300);log({first,generated,failure});
})().catch(error=>log({failure:error.message}));
'''.replace('PACE',str(pace))
    web.load_html('<p>PCM ficticio hacia una salida virtual, sin usar los auriculares.</p><script>let voiceVolume=1;'+(ROOT/'web/gemini-voice.js').read_text()+driver+'</script>','http://localhost/')
    GLib.timeout_add_seconds(18,lambda:(Gtk.main_quit(),False)[1]);Gtk.main();window.destroy()
    assert len(results)==1 and not results[0].get('failure'),results
    print(json.dumps(results[0]),flush=True)

def check_output():
    name='sw_stream_check_'+str(os.getpid())
    module=subprocess.check_output(['pactl','load-module','module-null-sink','sink_name='+name,'rate=24000','channels=1'],text=True).strip()
    try:
        for pace in (60,100):
            with tempfile.TemporaryFile() as output:
                capture=subprocess.Popen(['parec','--device='+name+'.monitor','--format=s16le','--rate=24000','--channels=1','--latency-msec=20'],stdout=output,stderr=subprocess.DEVNULL)
                try:
                    result=subprocess.run([sys.executable,__file__,'--browser',str(pace)],env={**os.environ,'PULSE_SINK':name},capture_output=True,text=True,timeout=22,cwd=ROOT)
                finally:capture.terminate();capture.wait(timeout=3)
                assert result.returncode==0,result.stderr[-2000:]
                timing=json.loads(result.stdout);assert 0<timing['first']<1000 and timing['first']<timing['generated'],timing
                output.seek(0);samples=[v[0] for v in struct.iter_unpack('<h',output.read())]
            peak=max(map(abs,samples),default=0);assert peak>300,'No llegó audio.'
            levels=[math.sqrt(sum(v*v for v in samples[i:i+240])/len(samples[i:i+240])) for i in range(0,len(samples),240)]
            active=[i for i,value in enumerate(levels) if value>peak*.1]
            assert 5950<=len(active)*10<=6100, 'Audio perdido o duplicado.'
            gaps=[];gap=0
            for value in levels[active[0]:active[-1]+1]:
                if value<peak*.1:gap+=10
                elif gap:gaps.append(gap);gap=0
            assert max(gaps,default=0)<=20 and sum(gaps)<=100,gaps
            print(f'OK paquetes cada {pace} ms: inicio {timing["first"]:.0f} ms, audio {len(active)*10} ms, pausas detectadas {gaps} ms.')
    finally:subprocess.run(['pactl','unload-module',module],check=True)

if __name__=='__main__':
    if '--browser' in sys.argv:browser(int(sys.argv[-1]))
    else:check_output()
