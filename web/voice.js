'use strict';
let voiceCapabilities={}, recording=null, transcribing=false, voiceGeneration=0, readingGeneration=0, readingAudio=null, readingURL=null, readingActive=false;
const voiceBusy=()=>!!recording||transcribing;
function voiceStatus(message){$('voice-status').textContent=message;}
function renderVoice(){
  $('dictate').disabled=!state||transcribing||!voiceCapabilities.dictation;
  $('dictate').textContent=recording?'■ Terminar dictado':'● Dictar respuesta';
  $('dictate').setAttribute('aria-pressed',String(!!recording));$('dictate-cancel').hidden=!recording;
  $('read-last').disabled=!voiceCapabilities.reading||!state?.runs.some(r=>r.status==='completed'&&r.text);
  $('read-stop').hidden=!readingActive;
  if(state)$('send').disabled=!!busy()||voiceBusy();
}
function stopReading(){readingGeneration++;readingActive=false;readingAudio?.pause();readingAudio=null;if(readingURL)URL.revokeObjectURL(readingURL);readingURL=null;renderVoice();}
async function readText(text){
  if(voiceBusy())throw new Error('Terminá el dictado antes de escuchar.');
  stopReading();readingActive=true;const generation=readingGeneration;
  const chunks=text.match(/[\s\S]{1,1200}(?:\s|$)|[\s\S]{1,1200}/g)||[];
  voiceStatus('Preparando lectura local…');$('read-stop').hidden=false;
  try {
    for(const chunk of chunks){
      if(generation!==readingGeneration)return;
      const blob=await api('/api/voice/read',{text:chunk});
      if(generation!==readingGeneration)return;
      readingURL=URL.createObjectURL(blob);readingAudio=new Audio(readingURL);renderVoice();voiceStatus('Leyendo en este equipo…');
      await new Promise((resolve,reject)=>{readingAudio.onended=resolve;readingAudio.onerror=()=>reject(new Error('No se pudo reproducir el audio.'));readingAudio.onpause=resolve;readingAudio.play().catch(reject);});
      if(generation!==readingGeneration)return;
      URL.revokeObjectURL(readingURL);readingURL=null;readingAudio=null;
    }
    voiceStatus('Lectura terminada.');
  } finally {if(generation===readingGeneration){stopReading();renderVoice();}}
}
function pcmBase64(parts){let text='';for(const part of parts){const bytes=new Uint8Array(part.buffer,part.byteOffset,part.byteLength);for(let i=0;i<bytes.length;i+=4096)text+=String.fromCharCode(...bytes.subarray(i,i+4096));}return btoa(text);}
async function releaseRecording(capture){
  clearTimeout(capture.timeout);clearInterval(capture.timer);capture.stream?.getTracks().forEach(track=>track.stop());
  capture.source?.disconnect();capture.node?.disconnect();if(capture.context && capture.context.state!=='closed')await capture.context.close();
}
async function cancelVoice(){
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
  if(!state||transcribing)return;
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
    capture.timeout=setTimeout(()=>finishDictation().catch(e=>voiceStatus(e.message)),45000);voiceStatus('Grabando. Pulsá Terminar dictado cuando quieras.');
  } catch(error){if(generation===voiceGeneration){await cancelVoice();voiceStatus(error.name==='NotAllowedError'?'Micrófono no autorizado. Podés responder escribiendo.':error.message);}else await releaseRecording(capture);}
}
$('dictate').onclick=action(startDictation);
$('dictate-cancel').onclick=action(async()=>{await cancelVoice();voiceStatus('Dictado descartado.');});
$('read-last').onclick=action(()=>readText(state.runs.findLast(r=>r.status==='completed'&&r.text).text));
$('read-stop').onclick=()=>{stopReading();voiceStatus('Lectura detenida.');};
$('runs').addEventListener('click',action(e=>{const button=e.target.closest('[data-read]');if(button)return readText(state.runs.find(r=>r.id===button.dataset.read).text);}));
let lastVoiceRun=null;
function updateVoice(){
  renderVoice();const run=state?.runs.at(-1);
  if(!run||run.id===lastVoiceRun||run.status!=='completed')return;
  lastVoiceRun=run.id;
  if($('auto-read').checked&&!voiceBusy())readText(run.text).catch(e=>voiceStatus(e.message));
}
function resetVoiceProject(){lastVoiceRun=state?.runs.at(-1)?.id||null;$('auto-read').checked=false;voiceStatus('Dictado español local; revisás el texto antes de enviarlo.');}
window.addEventListener('beforeunload',()=>{cancelVoice();});
api('/api/voice').then(value=>{voiceCapabilities=value;renderVoice();voiceStatus(value.dictation?'Dictado español local; revisás el texto antes de enviarlo.':'El dictado requiere el paquete de escritorio con voz.');if(!value.reading)voiceStatus($('voice-status').textContent+' No hay voz del sistema disponible.');}).catch(error=>voiceStatus(error.message));
