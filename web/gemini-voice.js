'use strict';
// Gemini Live usa PCM/WebSocket; comparte permisos y acciones con la voz WebRTC.
function sendGemini(session,message){if(realtime===session&&session.socket?.readyState===WebSocket.OPEN)session.socket.send(JSON.stringify(message));}
// WebKitGTK puede avanzar el reloj de Web Audio sin entregar PCM estable al dispositivo.
// Reutilizar la salida multimedia de la lectura local; otros motores conservan streaming.
const bufferedVoicePlayback=/Linux/.test(navigator.userAgent)&&/AppleWebKit/.test(navigator.userAgent)&&!/(Chrome|Chromium)/.test(navigator.userAgent);
function clearGeminiAudio(session){clearTimeout(session.pcmTimer);session.pcmTimer=null;for(const source of session.output||[])try{source.stop();}catch{}session.output?.clear();session.playAt=0;session.pcmParts=[];session.pcmBytes=0;session.queuedBytes=0;}
function flushGeminiAudio(session){
  clearTimeout(session.pcmTimer);session.pcmTimer=null;
  if(!session.pcmBytes)return;
  const size=session.pcmBytes,parts=session.pcmParts,header=new ArrayBuffer(44),view=new DataView(header);
  for(const [offset,text] of [[0,'RIFF'],[8,'WAVE'],[12,'fmt '],[36,'data']])for(let i=0;i<text.length;i++)view.setUint8(offset+i,text.charCodeAt(i));
  view.setUint32(4,36+size,true);view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);
  view.setUint32(24,24000,true);view.setUint32(28,48000,true);view.setUint16(32,2,true);view.setUint16(34,16,true);view.setUint32(40,size,true);
  const job={url:URL.createObjectURL(new Blob([header,...parts],{type:'audio/wav'})),bytes:size,chunks:parts.length};
  session.pcmParts=[];session.pcmBytes=0;
  job.stop=()=>{
    if(job.audio){job.audio.onended=job.audio.onerror=job.audio.ontimeupdate=null;job.audio.pause();job.audio.removeAttribute('src');job.audio.load();if(session.audio===job.audio)session.audio=null;}
    URL.revokeObjectURL(job.url);
  };
  session.output.add(job);
  // Preparar el siguiente bloque mientras suena el actual evita abrir su decodificador al terminar.
  job.audio=new Audio(job.url);job.audio.preload='auto';
  job.audio.onerror=()=>{if(session.output.has(job)){clearGeminiAudio(session);session.onPlaybackError?.(Error('No se pudo reproducir el audio del proveedor.'));}};
  job.audio.load();playBufferedVoice(session);
}
function playBufferedVoice(session){
  if(session.audio||!session.output.size)return;
  const job=session.output.values().next().value,audio=job.audio;session.audio=audio;audio.volume=voiceVolume;
  const failed=()=>{if(session.audio!==audio)return;clearGeminiAudio(session);session.onPlaybackError?.(Error('No se pudo reproducir el audio del proveedor.'));};
  audio.onerror=failed;
  audio.ontimeupdate=()=>{if(session.audio===audio&&session.output.size===1&&session.pcmBytes&&audio.duration-audio.currentTime<.3)flushGeminiAudio(session);};
  audio.onended=()=>{if(session.audio!==audio)return;job.stop();session.output.delete(job);session.queuedBytes-=job.bytes;if(session.stats)session.stats.played+=job.chunks;if(!session.output.size)flushGeminiAudio(session);playBufferedVoice(session);};
  audio.onplaying=()=>{if(session.audio===audio)session.onAudio?.();};
  audio.play().catch(failed);
}
function closeGeminiVoice(session){
  session.socket?.close();clearGeminiAudio(session);session.inputNode?.disconnect();session.inputSource?.disconnect();
  if(session.audioContext&&session.audioContext.state!=='closed')session.audioContext.close().catch(()=>{});
}
function playGeminiAudio(session,inline){
  if(!/^audio\/pcm(?:;rate=24000)?$/.test(inline.mimeType)||typeof inline.data!=='string'||inline.data.length>2000000)throw new Error('Formato de audio inesperado.');
  const binary=atob(inline.data);if(binary.length%2)throw new Error('Audio incompleto.');
  const bytes=Uint8Array.from(binary,c=>c.charCodeAt(0)),view=new DataView(bytes.buffer),samples=bytes.length/2;
  if(!samples)return;
  let peak=0;
  for(let i=0;i<samples;i++)peak=Math.max(peak,Math.abs(view.getInt16(i*2,true)/32768));
  if(session.stats){session.stats.chunks++;session.stats.seconds+=samples/24000;session.stats.peak=Math.max(session.stats.peak,peak);}
  if(bufferedVoicePlayback){
    // Inicio con hasta 1 s; después bloques de 2 s precargados. Todo en memoria y acotado.
    if((session.queuedBytes||0)+bytes.length>48000*90)throw Error('La respuesta de voz supera el límite de reproducción.');
    (session.pcmParts??=[]).push(bytes);session.pcmBytes=(session.pcmBytes||0)+bytes.length;session.queuedBytes=(session.queuedBytes||0)+bytes.length;
    if(session.pcmBytes>=48000*(session.audio?2:1))flushGeminiAudio(session);
    else if(session.audio)session.audio.ontimeupdate?.();
    else if(!session.audio&&!session.pcmTimer)session.pcmTimer=setTimeout(()=>{try{flushGeminiAudio(session);}catch(error){clearGeminiAudio(session);session.onPlaybackError?.(error);}},600);
    session.onAudio?.();return peak>0;
  }
  const context=session.audioContext;
  if((session.playAt||0)-context.currentTime>30)throw new Error('La reproducción no puede seguir el ritmo del audio.');
  const buffer=context.createBuffer(1,samples,24000),channel=buffer.getChannelData(0);
  for(let i=0;i<samples;i++)channel[i]=view.getInt16(i*2,true)/32768;
  if(!session.volumeNode){session.volumeNode=context.createGain();session.volumeNode.gain.value=voiceVolume;session.volumeNode.connect(context.destination);}
  const source=context.createBufferSource();source.buffer=buffer;source.connect(session.volumeNode);session.output.add(source);
  source.onended=()=>{session.output.delete(source);source.disconnect();if(session.stats&&!session.closed)session.stats.played++;};
  session.playAt=Math.max(context.currentTime,session.playAt||0);source.start(session.playAt);session.playAt+=buffer.duration;
  session.onAudio?.();
  return peak>0;
}
async function geminiEvent(session,event){
  if(realtime!==session)return;
  const raw=typeof event.data==='string'?event.data:new TextDecoder().decode(event.data);
  if(realtime!==session)return;
  if(raw.length>2000000)throw new Error('Respuesta de voz demasiado grande.');
  const data=JSON.parse(raw);
  if(session.signature!==realtimeSignature()){updateRealtime();return;}
  if(data.error)throw new Error('Gemini rechazó la sesión. Revisá acceso, cuota y facturación del proyecto en AI Studio.');
  if(data.setupComplete){session.ready=true;realtimeConnected(session);return;}
  const content=data.serverContent;
  if(session.relay){
    if(content?.inputTranscription)voiceTranscript(session,content.inputTranscription.text);
    if(content?.turnComplete)voiceTranscript(session,'',true);
    return; // Nunca reproducir ni ejecutar una respuesta propia de Gemini en Voz del chat.
  }
  if(content?.interrupted){clearGeminiAudio(session);$('realtime-caption').textContent='';}
  for(const part of content?.modelTurn?.parts||[])if(part.inlineData)playGeminiAudio(session,part.inlineData);
  if(content?.turnComplete||data.toolCall)flushGeminiAudio(session);
  if(content?.outputTranscription?.text)$('realtime-caption').textContent=($('realtime-caption').textContent+content.outputTranscription.text).slice(-8000);
  for(const id of data.toolCallCancellation?.ids||[])session.cancelled.add(id);
  // Las interrupciones de audio no esperan a una tarea HTTP pendiente.
  if(data.toolCall)session.queue=session.queue.then(async()=>{
    for(const call of data.toolCall.functionCalls||[]){
      if(realtime!==session||typeof call.id!=='string'||call.id.length>200||session.seen.has(call.id)||session.cancelled.has(call.id))continue;
      session.seen.add(call.id);session.currentCall=call.id;let response;
      try{if(JSON.stringify(call.args).length>20000)throw new Error('Argumentos demasiado grandes.');response=await runVoiceTool(session,call.name,call.args);}
      catch(error){response={error:error.message};}
      if(session.cancelled.has(call.id))continue;
      $('realtime-actions').textContent=response.error||response.next||(call.name==='get_context'?'Contexto consultado.':'Acción lista: '+call.args.action);
      sendGemini(session,{toolResponse:{functionResponses:[{id:call.id,name:call.name,response}]}});
    }
  }).catch(()=>{if(realtime===session)stopRealtime('No se pudo procesar la acción de Gemini.');});
}
async function startGeminiVoice(session){
  session.output=new Set();session.cancelled=new Set();
  session.onPlaybackError=error=>{if(realtime===session)stopRealtime(error.message);};
  session.audioContext=new AudioContext({sampleRate:16000});
  if(session.audioContext.sampleRate!==16000)throw new Error('Este dispositivo no permite el formato de voz.');
  await session.audioContext.audioWorklet.addModule('/voice-capture.js');
  if(realtime!==session)return;
  session.inputNode=new AudioWorkletNode(session.audioContext,'voice-capture');
  session.inputSource=session.audioContext.createMediaStreamSource(session.stream);
  session.inputSource.connect(session.inputNode);session.inputNode.connect(session.audioContext.destination);
  session.inputNode.port.onmessage=event=>{
    if(event.data==='end'){session.flushInput=false;if(!session.listening)sendGemini(session,{realtimeInput:{audioStreamEnd:true}});return;}
    if(!session.ready||realtime!==session||(!session.stream.getAudioTracks()[0]?.enabled&&!session.flushInput))return;
    if(session.socket.bufferedAmount>1000000){stopRealtime('La conexión no puede enviar el audio a tiempo. Micrófono cerrado.');return;}
    sendGemini(session,{realtimeInput:{audio:{mimeType:'audio/pcm;rate=16000',data:pcmBase64([event.data])}}});
  };
  await session.audioContext.resume();renderRealtime();
  const result=await api('/api/realtime/connect',{project:session.project,provider:'gemini',consent:true,actions:session.actions,relay:session.relay});
  if(realtime!==session)return;
  session.socket=new WebSocket('wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained?access_token='+encodeURIComponent(result.token));
  session.socket.binaryType='arraybuffer';
  session.socket.onopen=()=>sendGemini(session,{setup:result.setup});
  session.socket.onmessage=event=>{geminiEvent(session,event).catch(()=>{if(realtime===session)stopRealtime('Respuesta de Gemini inválida o no disponible. Revisá cuota y acceso en AI Studio.');});};
  session.socket.onerror=()=>{if(realtime===session)stopRealtime('No se pudo conectar con Gemini Live. Revisá conexión y acceso en AI Studio.');};
  session.socket.onclose=()=>{if(realtime===session)stopRealtime('Gemini cerró la sesión. Revisá cuota y acceso antes de reconectar.');};
}
