'use strict';
let voiceCapabilities={}, recording=null, transcribing=false, voiceGeneration=0, readingGeneration=0, readingAudio=null, readingURL=null, readingActive=false, onlineReading=null;
let voiceVolume=1;
function applyVoiceVolume(value){
  const level=Number(value);voiceVolume=Number.isFinite(level)&&level>=0&&level<=100?level/100:1;
  $('voice-volume').value=Math.round(voiceVolume*100);$('voice-volume-value').textContent=voiceVolume?Math.round(voiceVolume*100)+'%':'Silenciado';
  for(const session of [typeof realtime==='undefined'?null:realtime,onlineReading]){
    if(session?.volumeNode)session.volumeNode.gain.value=voiceVolume;
    if(session?.audio)session.audio.volume=voiceVolume;
  }
  if(readingAudio)readingAudio.volume=voiceVolume;
}
$('voice-volume').oninput=()=>{applyVoiceVolume($('voice-volume').value);try{localStorage.setItem('sw-voice-volume',$('voice-volume').value);}catch{}};
applyVoiceVolume(storedAppearance('sw-voice-volume','100'));
const remoteVoiceBusy=()=>typeof realtimeBusy==='function'&&realtimeBusy();
const voiceBusy=()=>!!recording||transcribing||remoteVoiceBusy();
function voiceStatus(message){$('voice-status').textContent=message;}
function renderVoice(){
  const online=$('realtime-enabled').checked,listening=!!recording||(remoteVoiceBusy()&&realtime.listening);
  $('dictate').disabled=!state||transcribing||(!online&&!voiceCapabilities.dictation);
  $('dictate').innerHTML=listening?'■':'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0014 0v-2M12 19v3M8 22h8"/></svg>';
  $('dictate').title=online?(listening?'Pausar escucha continua':'Activar escucha continua · mantené Espacio para hablar'):(recording?'Terminar dictado':'Dictar respuesta · mantené Espacio para hablar');$('dictate').setAttribute('aria-label',$('dictate').title);
  $('dictate').setAttribute('aria-pressed',String(listening));$('dictate-cancel').hidden=!recording;
  $('read-last').disabled=(!voiceCapabilities.reading&&!onlineReadingAllowed())||!currentRuns().some(r=>r.status==='completed'&&r.text);
  $('read-stop').hidden=!readingActive;
  if(state)$('send').disabled=!!busy()||!!recording||transcribing;
}
function onlineReadingAllowed(){return $('reading-mode')?.value!=='local'&&$('realtime-enabled').checked&&typeof realtimeConfigured!=='undefined'&&realtimeConfigured&&realtimeConsent;}
function stopReading(){readingGeneration++;onlineReading?.close();onlineReading=null;readingActive=false;readingAudio?.pause();readingAudio=null;if(readingURL)URL.revokeObjectURL(readingURL);readingURL=null;renderVoice();}
async function readText(text){
  if(recording||transcribing)throw new Error('Terminá el dictado antes de escuchar.');
  if(remoteVoiceBusy())stopRealtime('Conversación cerrada para escuchar el texto. Micrófono cerrado.');
  stopReading();readingActive=true;const generation=readingGeneration;
  const chunks=text.match(/[\s\S]{1,400}(?:\s|$)|[\s\S]{1,400}/gu)||[];
  let reader=null,fallback=false,fallbackReason='La lectura online no está disponible.';
  voiceStatus('Preparando lectura local…');$('read-stop').hidden=false;
  try {
    if(onlineReadingAllowed()){
      voiceStatus('Preparando lectura online · micrófono cerrado…');
      try{reader=await createOnlineReader(voiceProvider(),generation);}catch{fallback=true;}
    }
    for(const chunk of chunks){
      if(generation!==readingGeneration)return;
      if(reader){
        voiceStatus('Esperando audio de '+(reader.provider==='gemini'?'Gemini Live':'gpt-realtime')+' · micrófono cerrado…');
        try{await reader.read(chunk);continue;}catch(error){reader.close();reader=null;fallback=true;if(error.message==='No llegó audio.')fallbackReason='No llegó audio del proveedor.';}
        if(generation!==readingGeneration)return;
      }
      const blob=await api('/api/voice/read',{text:chunk});
      if(generation!==readingGeneration)return;
      readingURL=URL.createObjectURL(blob);readingAudio=new Audio(readingURL);readingAudio.volume=voiceVolume;renderVoice();voiceStatus(fallback?'Retomando el fragmento con voz local. '+fallbackReason:'Leyendo en este equipo…');
      await new Promise((resolve,reject)=>{readingAudio.onended=resolve;readingAudio.onerror=()=>reject(new Error('No se pudo reproducir el audio.'));readingAudio.onpause=resolve;readingAudio.play().catch(reject);});
      if(generation!==readingGeneration)return;
      URL.revokeObjectURL(readingURL);readingURL=null;readingAudio=null;
    }
    voiceStatus(fallback?'Lectura terminada con voz local de respaldo. '+fallbackReason:'Lectura terminada.');
  } finally {if(generation===readingGeneration){stopReading();renderVoice();}}
}
// Sesión de lectura sin micrófono, herramientas, fuentes ni historial editorial.
async function createOnlineReader(provider,generation){
  const session={provider,audioContext:new AudioContext(),output:new Set(),playAt:0,closed:false,pending:null,stats:{chunks:0,seconds:0,peak:0,played:0,transcript:''}};
  onlineReading=session;
  const cancelled=()=>session.closed||generation!==readingGeneration;
  session.close=(error=Error('Lectura cerrada.'))=>{if(session.closed)return;session.closed=true;clearTimeout(session.limit);clearTimeout(session.connectTimer);clearInterval(session.drain);session.rejectReady?.(error);session.pending?.reject(error);session.pending=null;session.socket?.close();clearGeminiAudio(session);if(session.audioContext.state!=='closed')session.audioContext.close().catch(()=>{});};
  const fail=error=>session.close(error instanceof Error?error:Error('Se interrumpió la conexión de voz.'));
  const ready=new Promise((resolve,reject)=>{session.resolveReady=resolve;session.rejectReady=reject;});
  session.connectTimer=setTimeout(fail,30000);
  try{
    // Incluye la activación de audio en el plazo y permite cancelarla si el motor la bloquea.
    await Promise.race([session.audioContext.resume(),ready]);
    if(cancelled())throw Error('Lectura cancelada.');
    const connection=await api('/api/realtime/read-session',{provider,consent:true});
    if(cancelled())throw Error('Lectura cancelada.');
    session.socket=provider==='gemini'
      ?new WebSocket('wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained?access_token='+encodeURIComponent(connection.token))
      :new WebSocket('wss://api.openai.com/v1/realtime?model='+encodeURIComponent(connection.model),['realtime','openai-insecure-api-key.'+connection.token]);
    session.socket.binaryType='arraybuffer';
    session.limit=setTimeout(fail,600000);
    session.socket.onerror=()=>fail(Error('No se pudo mantener la conexión de voz.'));
    session.socket.onclose=event=>fail(Error(`El proveedor cerró la sesión de voz${Number.isInteger(event?.code)?' (código '+event.code+')':''}.`));
    session.socket.onopen=()=>{if(provider==='gemini')session.socket.send(JSON.stringify({setup:connection.setup}));};
    session.queue=Promise.resolve();
    session.socket.onmessage=event=>{session.queue=session.queue.then(async()=>{
      if(cancelled())return;
      const raw=typeof event.data==='string'?event.data:new TextDecoder().decode(event.data);
      if(cancelled())return;
      if(raw.length>2000000)throw Error('Respuesta demasiado grande.');
      const data=JSON.parse(raw);
      if(data.error||data.type==='error'||data.toolCall||data.type==='response.function_call_arguments.done')throw Error('Respuesta de lectura inválida.');
      if(data.setupComplete||data.type==='session.created'){clearTimeout(session.connectTimer);session.resolveReady();return;}
      const pending=session.pending;if(!pending)return;
      if(data.serverContent?.outputTranscription?.text){session.stats.transcript=(session.stats.transcript+data.serverContent.outputTranscription.text).slice(-2000);session.onAudio?.();}
      const audio=provider==='gemini'?(data.serverContent?.modelTurn?.parts||[]).filter(p=>p.inlineData).map(p=>p.inlineData):data.type==='response.output_audio.delta'?[{mimeType:'audio/pcm;rate=24000',data:data.delta}]:[];
      for(const part of audio)if(playGeminiAudio(session,part)){
        pending.received=true;clearTimeout(pending.firstAudio);
        voiceStatus('Leyendo con '+(provider==='gemini'?'Gemini Live':'gpt-realtime')+' · micrófono cerrado…');
      }
      if(data.serverContent?.interrupted)throw Error('Lectura interrumpida.');
      if(data.type==='response.done'){
        if(data.response?.status!=='completed')throw Error('Lectura incompleta.');
        pending.done=true;
      }
      if(data.serverContent?.turnComplete)pending.done=true;
      if(pending.done&&!pending.received)throw Error('No llegó audio.');
    }).catch(fail);};
    await ready;
    if(cancelled())throw Error('Lectura cancelada.');
    session.read=text=>new Promise((resolve,reject)=>{
      if(cancelled()){reject(Error('Lectura cerrada.'));return;}
      session.pending={resolve,reject,received:false,done:false};
      session.pending.firstAudio=setTimeout(()=>fail(Error('No llegó audio.')),15000);
      const timeout=setTimeout(fail,90000);
      session.drain=setInterval(()=>{const p=session.pending;if(p?.done&&!session.output.size){clearTimeout(timeout);clearInterval(session.drain);session.pending=null;p.resolve();}},40);
      // Al cerrar se cancela también la espera del fragmento actual.
      session.pending.reject=error=>{clearTimeout(session.pending?.firstAudio);clearTimeout(timeout);clearInterval(session.drain);reject(error);};
      const message=provider==='gemini'?{realtimeInput:{text}}:{type:'response.create',response:{conversation:'none',output_modalities:['audio'],tools:[],tool_choice:'none',input:[{type:'message',role:'user',content:[{type:'input_text',text}]}]}};
      try{session.socket.send(JSON.stringify(message));}catch{fail();}
    });
    return session;
  }catch(error){session.close();throw error;}
}
function showVoiceTest(reader,message){
  const stats=reader?.stats;
  $('voice-test-status').textContent=message;
  $('voice-test-details').textContent=stats?`Audio recibido: ${stats.chunks} fragmentos · ${stats.seconds.toFixed(1)} s · señal máxima ${(stats.peak*100).toFixed(1)}% · procesados por el reproductor: ${stats.played}. Motor de audio: ${reader.audioContext.state}. Volumen: ${Math.round(voiceVolume*100)}%.${stats.transcript?' Texto devuelto: '+stats.transcript:''}`:'';
}
$('voice-test').onclick=action(async()=>{
  const provider=voiceProvider(),label=provider==='gemini'?'Gemini Live':'OpenAI Realtime';
  showVoiceTest(null,'');
  if(!realtimeConfigured||!realtimeConsent){showVoiceTest(null,'Guardá la clave y los permisos del proveedor en Asistente de voz online antes de probar.');return;}
  if(!voiceVolume){showVoiceTest(null,'El volumen está en 0%. Subilo antes de probar la voz.');return;}
  if(recording||transcribing){showVoiceTest(null,'Terminá el dictado antes de probar.');return;}
  if(remoteVoiceBusy())stopRealtime('Conversación cerrada para probar la salida de voz. Micrófono cerrado.');
  stopReading();readingActive=true;const generation=readingGeneration;
  $('voice-test-stop').hidden=false;showVoiceTest(null,'Conectando con '+label+'…');
  let reader;
  try{
    reader=await createOnlineReader(provider,generation);
    reader.onAudio=()=>{if(generation===readingGeneration)showVoiceTest(reader,reader.stats.peak>0?'Audio de '+label+' recibido; reproduciendo…':'Respuesta de '+label+' recibida; esperando audio con señal…');};
    showVoiceTest(reader,'Conectado con '+label+'. Esperando audio…');
    await reader.read('Esta es una prueba de voz de Story Workbench. La nave azul descansa junto al faro.');
    if(generation===readingGeneration)showVoiceTest(reader,'Prueba terminada con '+label+'. Si no escuchaste nada, revisá la salida de sonido de la app y del sistema.');
  }catch(error){
    showVoiceTest(reader,generation!==readingGeneration?'Prueba cancelada.':'No se completó la prueba con '+label+': '+error.message+' No se usó la voz local.');
  }finally{
    reader?.close();if(generation===readingGeneration)stopReading();$('voice-test-stop').hidden=true;
  }
});
$('voice-test-stop').onclick=()=>stopReading();
function pcmBase64(parts){let text='';for(const part of parts){const bytes=new Uint8Array(part.buffer,part.byteOffset,part.byteLength);for(let i=0;i<bytes.length;i+=4096)text+=String.fromCharCode(...bytes.subarray(i,i+4096));}return btoa(text);}
async function releaseRecording(capture){
  clearTimeout(capture.timeout);clearInterval(capture.timer);capture.stream?.getTracks().forEach(track=>track.stop());
  capture.source?.disconnect();capture.node?.disconnect();if(capture.context && capture.context.state!=='closed')await capture.context.close();
}
async function cancelVoice(){
  if(remoteVoiceBusy())stopRealtime();
  voiceGeneration++;const capture=recording;recording=null;transcribing=false;
  if(capture)await releaseRecording(capture);stopReading();renderVoice();
}
async function finishDictation(){
  const capture=recording;if(!capture||!capture.node)return;
  recording=null;transcribing=true;renderVoice();voiceStatus('Transcribiendo en este equipo…');
  // Vaciar el último bloque parcial antes de cerrar el AudioContext.
  capture.node.port.postMessage('flush');await new Promise(resolve=>setTimeout(resolve,60));
  await releaseRecording(capture);
  const generation=capture.generation;
  try {
    const result=await api('/api/voice/transcribe',{pcm:pcmBase64(capture.parts)});
    if(generation!==voiceGeneration||capture.project!==state?.id)return;
    if(result.text){const prompt=$('prompt');prompt.focus();prompt.setSelectionRange(prompt.value.length,prompt.value.length);document.execCommand('insertText',false,(prompt.value.trim()?'\n':'')+result.text);voiceStatus('Transcripción lista. Corregila si hace falta y pulsá Enviar.');}
    else voiceStatus('No se reconocieron palabras. Probá hablar más cerca del micrófono.');
  } finally {if(generation===voiceGeneration){transcribing=false;renderVoice();}}
}
async function startDictation(){
  if(recording)return finishDictation();
  if(!state||transcribing||remoteVoiceBusy())return;
  stopReading();const generation=++voiceGeneration;
  const capture={project:state.id,generation,parts:[],samples:0};recording=capture;renderVoice();voiceStatus('Esperando permiso del micrófono…');
  try {
    capture.stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true},video:false});
    if(generation!==voiceGeneration){await releaseRecording(capture);return;}
    capture.context=new AudioContext({sampleRate:16000});
    if(capture.context.sampleRate!==16000)throw new Error('Este dispositivo no permite el formato de dictado.');
    await capture.context.audioWorklet.addModule('/voice-capture.js');
    if(generation!==voiceGeneration){await releaseRecording(capture);return;}
    capture.node=new AudioWorkletNode(capture.context,'voice-capture');
    capture.node.port.onmessage=event=>{const part=event.data.subarray(0,Math.max(0,16000*45-capture.samples));capture.samples+=part.length;if(part.length)capture.parts.push(part);};
    capture.source=capture.context.createMediaStreamSource(capture.stream);capture.source.connect(capture.node);capture.node.connect(capture.context.destination);
    await capture.context.resume();const started=Date.now();
    capture.timer=setInterval(()=>voiceStatus(`Grabando · ${Math.min(45,Math.floor((Date.now()-started)/1000))} / 45 segundos. No se envía a ChatGPT.`),500);
    capture.timeout=setTimeout(()=>finishDictation().catch(e=>voiceStatus(e.message)),45000);voiceStatus('Grabando. Volvé a pulsar el micrófono para terminar.');
  } catch(error){if(generation===voiceGeneration){await cancelVoice();voiceStatus(error.name==='NotAllowedError'?'Micrófono no autorizado. Podés responder escribiendo.':error.message);}else await releaseRecording(capture);}
}
$('dictate').onclick=action(async()=>{if($('realtime-enabled').checked){if(!realtimeConfigured||!realtimeConsent){openVoiceSettings();return;}if(realtime)setVoiceListening(!realtime.listening,!realtime.listening);else await startRealtime();}else await startDictation();});
$('dictate-cancel').onclick=action(async()=>{await cancelVoice();voiceStatus('Dictado descartado.');});
$('read-last').onclick=action(()=>readText(currentRuns().findLast(r=>r.status==='completed'&&r.text).text));
$('read-stop').onclick=()=>{stopReading();voiceStatus('Lectura detenida.');};
$('auto-read').onchange=()=>{if(!$('auto-read').checked){stopReading();voiceStatus('Lectura automática desactivada.');}};
$('runs').addEventListener('click',action(e=>{const button=e.target.closest('[data-read]');if(button)return readText(state.runs.find(r=>r.id===button.dataset.read).text);}));
let lastVoiceRun=null;
function updateVoice(){
  renderVoice();const run=currentRuns().at(-1);
  if(!run||run.id===lastVoiceRun||run.status!=='completed')return;
  if($('auto-read').checked&&(recording||transcribing))return;
  lastVoiceRun=run.id;
  if($('auto-read').checked)readText(run.text).catch(e=>voiceStatus(e.message));
}
function resetVoiceProject(){lastVoiceRun=currentRuns().at(-1)?.id||null;$('auto-read').checked=false;voiceStatus('Dictado español local; revisás el texto antes de enviarlo.');}
window.addEventListener('beforeunload',()=>{cancelVoice();});
api('/api/voice').then(value=>{voiceCapabilities=value;renderVoice();voiceStatus(value.dictation?'Dictado español local; revisás el texto antes de enviarlo.':'El dictado requiere el paquete de escritorio con voz.');if(!value.reading)voiceStatus($('voice-status').textContent+' No hay voz del sistema disponible.');}).catch(error=>voiceStatus(error.message));

let spaceListening=false;
function releaseSpace(){
  if(!spaceListening)return;spaceListening=false;
  if(remoteVoiceBusy()&&!realtime.continuous)setVoiceListening(false);
  if(recording?.pushToTalk){if(recording.node)finishDictation().catch(e=>voiceStatus(e.message));else cancelVoice();}
}
window.addEventListener('keydown',event=>{
  if(event.code==='Space'&&event.repeat&&spaceListening){event.preventDefault();return;}
  if(event.code!=='Space'||event.repeat||event.ctrlKey||event.metaKey||event.altKey||event.shiftKey||!state||$('prompt').value.length||document.querySelector('dialog[open]'))return;
  const focused=document.activeElement;
  if(focused!==$('prompt')&&focused!==$('dictate')&&(focused?.matches('input,textarea,select,button,a,summary')||focused?.isContentEditable))return;
  if(recording||transcribing||(remoteVoiceBusy()&&realtime.listening)){if(focused===$('dictate'))event.preventDefault();return;}
  event.preventDefault();spaceListening=true;
  if($('realtime-enabled').checked){
    if(!realtimeConfigured||!realtimeConsent){spaceListening=false;openVoiceSettings();return;}
    if(realtime)setVoiceListening(true,false);else startRealtime({pushToTalk:true}).catch(e=>voiceStatus(e.message));
  }else{startDictation().catch(e=>voiceStatus(e.message));if(recording)recording.pushToTalk=true;}
});
window.addEventListener('keyup',event=>{if(event.code==='Space')releaseSpace();});
window.addEventListener('blur',releaseSpace);

$('reading-mode').onchange=()=>{stopReading();try{localStorage.setItem('sw-reading-mode',$('reading-mode').value);}catch{}};
try{if(localStorage.getItem('sw-reading-mode')==='local')$('reading-mode').value='local';}catch{}
