'use strict';
let realtime=null, realtimeConfigured=false, realtimeConsent=false, realtimeProviders={};
const realtimeBusy=()=>!!realtime;
const realtimeSignature=()=>JSON.stringify([state.id,state.history_start,state.purpose,state.engine,state.translation_config,state.documents.filter(d=>d.selected).map(d=>[d.id,d.hash])]);
const voiceProvider=()=>$('realtime-provider').value;
function realtimeStatus(message){$('realtime-status').textContent=message;}
function renderRealtime(){
  if($('voice-session'))$('voice-session').hidden=!realtime;
  $('realtime-start').hidden=!$('realtime-enabled').checked||!!realtime;
  $('realtime-global-stop').hidden=!realtime;
  $('realtime-stop').hidden=!realtime;$('realtime-mute').hidden=!realtime?.stream;
  $('realtime-start').disabled=!state||!realtimeConfigured||!realtimeConsent;
  renderVoice();
}
function stopRealtime(message='Conversación terminada. Micrófono cerrado.'){
  if(onlineReading)stopReading();
  const session=realtime;realtime=null;
  if(session){if(session.provider==='gemini')closeGeminiVoice(session);clearTimeout(session.timeout);clearTimeout(session.transcriptTimer);clearInterval(session.timer);session.stream?.getTracks().forEach(t=>t.stop());session.channel?.close();session.pc?.close();session.audio?.pause();if(session.audio)session.audio.srcObject=null;}
  realtimeStatus(message);$('realtime-mute').textContent='Pausar micrófono';$('realtime-mute').setAttribute('aria-pressed','false');renderRealtime();
}
function updateRealtime(){
  if(realtime&&realtime.signature!==realtimeSignature())stopRealtime('Cambió el proyecto o sus fuentes. Volvé a conectar para usar el contexto actualizado.');
  renderRealtime();
}
function sendRealtime(session,event){if(realtime===session&&session.channel?.readyState==='open')session.channel.send(JSON.stringify(event));}
async function realtimeAction(session,args){
  if(realtime!==session||state?.id!==session.project)throw new Error('La sesión ya terminó.');
  if(!session.actions)throw new Error('El autor no habilitó acciones.');
  if(!args||Object.keys(args).sort().join(',')!=='action,mode,target,text'||Object.values(args).some(v=>typeof v!=='string')||args.text.length>12000||args.target.length>100)throw new Error('Acción inválida.');
  const {action:operation,target,mode,text}=args;
  if(operation==='navigate'){
    await navigateWorkbench(target);
    return {visible:target};
  }
  if(operation==='set_theme'){
    if(!['system','light','dark'].includes(target))throw new Error('Tema inválido.');
    $('theme').value=themeOption(target);$('theme').onchange();return {theme:target};
  }
  if(operation==='open_document'){
    if(dirty)throw new Error('Guardá el documento actual antes de cambiar.');
    if(!state.documents.some(d=>d.id===target))throw new Error('Documento inexistente.');
    showMaterial();openDocument(target);return {opened:target};
  }
  if(operation==='prepare_decision'){
    if(!text.trim()||text.length>4000)throw new Error('Criterio vacío o demasiado largo.');
    if($('decision-text').value.trim())throw new Error('Ya hay una decisión sin registrar.');
    $('decision-text').value=text;$('decision-status').value='pending';showPanel('decisions');
    return {prepared:true,registered:false,next:'El autor debe revisar y pulsar Registrar.'};
  }
  if(!['prepare_task','start_task'].includes(operation))throw new Error('Acción no permitida. Aprobar, guardar o borrar textos requiere los controles manuales.');
  if(!['interview','draft','diagnosis','impact','proposal','summary','chat','translate'].includes(mode)||!text.trim())throw new Error('Tarea inválida.');
  if((mode==='translate'&&state.purpose!=='translation')||(mode==='draft'&&state.purpose==='translation'))throw new Error('Usá el flujo de traducción y revisión.');
  if(operation==='prepare_task'){
    if($('prompt').value.trim()&&$('prompt').value!==text)throw new Error('Ya hay un mensaje sin enviar. No se reemplazó.');
    $('mode').value=mode;setTaskMode();$('prompt').value=text;savePromptDraft();showPanel('conversation');return {prepared:true,sent:false};
  }
  if(dirty)throw new Error('Guardá primero los cambios del documento; El motor editorial recibe la versión guardada.');
  if(busy())throw new Error('Ya hay una tarea en curso.');
  if(!await engineReady())throw new Error('Configurá el motor editorial elegido para lanzar tareas.');
  if(realtime!==session||state.id!==session.project||session.signature!==realtimeSignature())throw new Error('La sesión cambió antes del envío.');
  if(session.cancelled?.has(session.currentCall))throw new Error('La petición oral fue interrumpida antes del envío.');
  const run=await api('/api/run',{project:session.project,mode,prompt:text,skill:$('skill').checked});
  startTyping(run.id);
  if(realtime===session){showPanel('conversation');await poll();}
  return {started:true,run:run.id,next:'El resultado quedará en la conversación editorial. Consultá get_context para leerlo cuando termine; no está aprobado.'};
}
async function runVoiceTool(session,name,args){
  if(realtime!==session||session.signature!==realtimeSignature())throw new Error('La sesión o sus fuentes cambiaron.');
  if(name==='get_context'){
    if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).length)throw new Error('Consulta inválida.');
    return api(`/api/projects/${session.project}/voice-context`);
  }
  if(name==='workbench_action')return realtimeAction(session,args);
  throw new Error('Función no permitida.');
}
// La transcripción pasa por el mismo envío que el teclado; el proveedor de voz no decide la respuesta.
function syncVoiceMicrophone(session){
  if(realtime!==session)return;
  session.stream?.getAudioTracks().forEach(track=>track.enabled=!!session.listening&&!session.waiting&&!session.speaking);
  renderVoice();
}
function updateVoiceChat(){
  const session=realtime;if(!session?.relayRun)return;
  const run=currentRuns().find(r=>r.id===session.relayRun);
  if(!run||!['completed','failed','cancelled','interrupted'].includes(run.status))return;
  session.relayRun=null;session.waiting=false;syncVoiceMicrophone(session);
}
async function relayVoiceText(session,text){
  if(realtime!==session||session.signature!==realtimeSignature()||!text.trim())return;
  const existing=$('prompt').value;
  $('prompt').value=existing+(existing.trim()?'\n':'')+text.trim();savePromptDraft();showPanel('conversation');
  $('realtime-caption').textContent='Transcripción: '+text.trim();
  if(!session.actions||existing.trim()||busy()||session.waiting||dirty){
    setVoiceListening(false);voiceStatus('Transcripción en Tu mensaje. Revisala y pulsá Enviar; no se reemplazó ni envió otro borrador.');return;
  }
  session.waiting=true;syncVoiceMicrophone(session);voiceStatus('Mensaje de voz enviado al chat. Esperando al motor editorial…');
  try{
    const run=await sendChatMessage($('prompt').value,()=>realtime===session&&session.signature===realtimeSignature());
    if(realtime!==session)return;
    session.relayRun=run?.id;
    if(!run){session.waiting=false;setVoiceListening(false);voiceStatus('Mensaje sin enviar. Revisá la conexión y pulsá Enviar.');}
    updateVoiceChat();
  }catch(error){if(realtime===session){session.waiting=false;setVoiceListening(false);voiceStatus(error.message+' La transcripción quedó en Tu mensaje.');notice(error.message,true);}}
}
function voiceTranscript(session,text,finished=false){
  if(realtime!==session||!session.relay)return;
  if(typeof text==='string'){
    session.transcript=(session.transcript||'')+text;
    if(session.transcript.length>12000){$('prompt').value+=($('prompt').value?'\n':'')+session.transcript;savePromptDraft();stopRealtime('Dictado demasiado largo. Quedó en Tu mensaje para dividirlo antes de enviar.');return;}
    $('realtime-caption').textContent='Escuché: '+session.transcript;
  }
  if(finished)session.transcriptEnded=true;
  if(!session.transcriptEnded||!session.transcript?.trim())return;
  clearTimeout(session.transcriptTimer);
  // Gemini no ordena transcripción y turnComplete; reunir los fragmentos tardíos antes del envío.
  session.transcriptTimer=setTimeout(()=>{
    const value=session.transcript;session.transcript='';session.transcriptEnded=false;
    relayVoiceText(session,value).catch(error=>{if(realtime===session)notice(error.message,true);});
  },session.provider==='gemini'?600:0);
}
function realtimeConnected(session){
  if(realtime!==session)return;
  clearTimeout(session.timeout);const started=Date.now();
  session.timeout=setTimeout(()=>{if(realtime===session)stopRealtime('Se alcanzaron 10 minutos. Podés iniciar otra conversación.');},600000);
  const status=()=>realtimeStatus(`${session.provider==='gemini'?'Gemini Live':'gpt-realtime'} · API activa · ${Math.floor((Date.now()-started)/1000)} s / 600 s${session.stream.getAudioTracks()[0]?.enabled?' · micrófono abierto':' · micrófono pausado'}`);
  status();session.timer=setInterval(status,1000);
}
async function realtimeEvent(session,event){
  if(realtime!==session||typeof event.data!=='string'||event.data.length>2000000)return;
  if(session.signature!==realtimeSignature()){updateRealtime();return;}
  const data=JSON.parse(event.data);
  if(session.relay&&data.type==='conversation.item.input_audio_transcription.completed'){
    if(typeof data.item_id!=='string'||session.seen.has(data.item_id))return;session.seen.add(data.item_id);voiceTranscript(session,data.transcript,true);return;
  }
  if(session.relay&&data.type==='conversation.item.input_audio_transcription.failed'){voiceStatus('No se pudo transcribir. Volvé a hablar o escribí el mensaje.');return;}
  if(data.type==='error'){stopRealtime('La sesión de voz informó un error. Revisá conexión y cuota antes de reconectar.');return;}
  if(session.relay)return;
  if(['response.output_audio_transcript.delta','response.audio_transcript.delta'].includes(data.type)&&typeof data.delta==='string'){
    $('realtime-caption').textContent=($('realtime-caption').textContent+data.delta).slice(-8000);
  }
  if(data.type==='response.created')$('realtime-caption').textContent='';
  if(data.type!=='response.done'||data.response?.status!=='completed')return;
  let answered=false;
  for(const call of data.response.output||[]){
    if(call.type!=='function_call'||typeof call.call_id!=='string'||call.call_id.length>200||session.seen.has(call.call_id))continue;
    session.seen.add(call.call_id);answered=true;let result;
    try{
      if(typeof call.arguments!=='string'||call.arguments.length>20000)throw new Error('Argumentos inválidos.');
      const args=JSON.parse(call.arguments);
      result=await runVoiceTool(session,call.name,args);
      $('realtime-actions').textContent=call.name==='get_context'?'Contexto consultado.':'Acción: '+args.action+' · '+(result.next||'Lista.');
    }catch(error){result={error:error.message};$('realtime-actions').textContent=error.message;}
    sendRealtime(session,{type:'conversation.item.create',item:{type:'function_call_output',call_id:call.call_id,output:JSON.stringify(result)}});
  }
  if(answered)sendRealtime(session,{type:'response.create'});
}
async function startRealtime(options={}){
  if(realtime||!state)return;
  if(!realtimeConfigured||!realtimeConsent||!$('realtime-enabled').checked)throw new Error('Configurá la clave y aceptá el uso de la API antes de conectar.');
  if(voiceProvider()==='openai'&&typeof RTCPeerConnection!=='function')throw new Error('La voz de OpenAI no está disponible en este entorno. Podés usar dictado local o probar Gemini Live.');
  $('settings-dialog')?.close();$('realtime-dialog').close();
  await cancelVoice();
  const session={relay:$('voice-mode').value==='chat',listening:!options.pushToTalk||spaceListening,continuous:!options.pushToTalk,provider:voiceProvider(),project:state.id,signature:realtimeSignature(),actions:$('realtime-allow-actions').checked,seen:new Set(),queue:Promise.resolve()};
  realtime=session;if(session.relay)$('auto-read').checked=true;realtimeStatus(session.provider==='gemini'?'Conectando Gemini Live…':'Conectando gpt-realtime…');renderRealtime();
  session.timeout=setTimeout(()=>{if(realtime===session)stopRealtime('La conexión tardó demasiado. Micrófono cerrado.');},45000);
  try{
    session.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true},video:false});
    if(realtime!==session){session.stream.getTracks().forEach(t=>t.stop());return;}
    session.stream.getAudioTracks().forEach(t=>t.enabled=session.listening);
    if(session.provider==='gemini'){await startGeminiVoice(session);return;}
    session.pc=new RTCPeerConnection();session.audio=new Audio();session.audio.volume=voiceVolume;session.audio.autoplay=true;
    session.pc.ontrack=e=>{if(realtime===session){if(session.relay)return;session.audio.srcObject=e.streams[0];session.audio.play().catch(()=>{if(realtime===session)stopRealtime('No se pudo reproducir la voz. Volvé a conectar.');});}};
    session.pc.onconnectionstatechange=()=>{if(realtime===session&&['failed','disconnected','closed'].includes(session.pc.connectionState))stopRealtime('Conexión de voz cerrada. Podés reconectar manualmente.');};
    session.stream.getTracks().forEach(track=>session.pc.addTrack(track,session.stream));
    session.channel=session.pc.createDataChannel('oai-events');
    session.channel.onmessage=event=>{session.queue=session.queue.then(()=>realtimeEvent(session,event)).catch(()=>{if(realtime===session)stopRealtime('Respuesta de voz inválida. Micrófono cerrado.');});};
    session.channel.onclose=()=>{if(realtime===session)stopRealtime('El servicio cerró la conversación. Micrófono cerrado.');};
    session.channel.onopen=()=>realtimeConnected(session);
    renderRealtime();const offer=await session.pc.createOffer();
    if(realtime!==session)return;
    await session.pc.setLocalDescription(offer);
    const answer=await api('/api/realtime/connect',{project:session.project,sdp:offer.sdp,consent:true,actions:session.actions,relay:session.relay});
    if(realtime!==session)return;
    await session.pc.setRemoteDescription({type:'answer',sdp:answer.sdp});
  }catch(error){if(realtime===session)stopRealtime(error.name==='NotAllowedError'?'Micrófono no autorizado. Podés seguir escribiendo.':error.message);}
}
$('realtime-enabled').onchange=()=>{
  if(!$('realtime-enabled').checked)stopRealtime('Desactivado. El dictado sigue siendo local.');
  else if(!realtimeConfigured||!realtimeConsent)openVoiceSettings();
  renderRealtime();
};
function updateVoiceProviderNote(){$('realtime-provider-note').textContent=voiceProvider()==='gemini'?'Modelo: gemini-3.1-flash-live-preview. Usa una clave de Google AI Studio. AI Plus y la API son servicios separados; acceso, cuota y posibles cargos dependen del proyecto de la clave. Gemini puede operar la app sin una clave OpenAI. La lectura usa gemini-3.1-flash-tts-preview (Kore), dedicado a leer el texto. Las tareas editoriales siguen usando el motor elegido.':'Modelo: gpt-realtime. La API se factura por separado. Esta versión de Codex no admite Realtime con la sesión ChatGPT. La lectura usa gpt-4o-mini-tts (Marin) con la misma clave. No hay cambio automático a pago.';}
function openVoiceSettings(){updateVoiceProviderNote();refreshVoiceStorage().catch(e=>notice(e.message,true));showDialog($('realtime-dialog'));}
$('realtime-settings').onclick=openVoiceSettings;
$('realtime-dialog').addEventListener('close',()=>{$('realtime-key').value='';});
$('realtime-close').onclick=()=>{$('realtime-dialog').close();};
$('realtime-consent').onchange=()=>{realtimeConsent=false;stopRealtime('Guardá el consentimiento para volver a conectar.');};
$('realtime-allow-actions').onchange=()=>{stopRealtime('Permisos cambiados. Volvé a conectar para aplicarlos.');};
$('realtime-save').onclick=action(async()=>{
  try{
  if(!$('realtime-consent').checked)throw new Error('Confirmá el envío al proveedor y las condiciones de la API antes de habilitarlo.');
  stopRealtime();
  const key=$('realtime-key').value.trim(),remember=$('realtime-remember').checked;$('realtime-key').value='';
  if(key){const result=await api('/api/realtime/key',{key,provider:voiceProvider(),remember});realtimeProviders=result.providers;realtimeConfigured=realtimeProviders[voiceProvider()];}
  if(!key&&voiceStorage.available)await api('/api/voice-storage',{provider:voiceProvider(),remember});
  if(!realtimeConfigured)throw new Error('Falta una clave API. Ingresala en este diálogo.');
  realtimeConsent=true;$('realtime-enabled').checked=true;await refreshVoiceStorage();$('realtime-dialog').close();$('settings-dialog')?.close();realtimeStatus('Configurado. Pulsá el micrófono del chat para conectar, o mantené Espacio para hablar.');renderRealtime();
  }catch(error){try{const status=await api('/api/realtime');realtimeProviders=status.providers;realtimeConfigured=!!realtimeProviders[voiceProvider()];await refreshVoiceStorage();renderRealtime();}catch{}throw error;}
});
$('realtime-forget').onclick=action(async()=>{
  stopRealtime();const result=await api('/api/realtime/key',{key:'',provider:voiceProvider()});realtimeProviders=result.providers;realtimeConfigured=realtimeProviders[voiceProvider()];
  realtimeConsent=false;$('realtime-consent').checked=false;$('realtime-key').value='';$('realtime-enabled').checked=false;
  await refreshVoiceStorage();realtimeStatus('Clave olvidada. Realtime desactivado.');renderRealtime();
});
$('realtime-start').onclick=action(startRealtime);
$('realtime-stop').onclick=$('realtime-global-stop').onclick=()=>stopRealtime();
function setVoiceListening(enabled,continuous=false){
  if(!realtime)return;realtime.listening=enabled;realtime.continuous=continuous;
  if(enabled&&realtime.relay&&readingActive)stopReading();
  syncVoiceMicrophone(realtime);
  if(realtime.provider==='gemini'&&!enabled&&realtime.inputNode){realtime.flushInput=true;realtime.inputNode.port.postMessage('end');}
  $('realtime-mute').setAttribute('aria-pressed',String(!enabled));$('realtime-mute').textContent=enabled?'Pausar micrófono':'Reactivar micrófono';renderVoice();
}
$('realtime-mute').onclick=()=>{if(realtime)setVoiceListening(!realtime.listening,!realtime.listening);};
let voiceStorage={available:false,stored:{}};
async function refreshVoiceStorage(){
  voiceStorage=await api('/api/voice-storage');$('realtime-remember').disabled=!voiceStorage.available;
  $('realtime-remember').checked=!!voiceStorage.stored[voiceProvider()];$('realtime-storage-status').textContent=voiceStorage.reason;
  $('realtime-key-status').textContent=realtimeConfigured?(voiceStorage.stored[voiceProvider()]?'Clave guardada cifrada. No hace falta volver a ingresarla.':'Clave disponible solo en memoria.'):'No hay clave configurada para este proveedor.';
}
$('realtime-provider').onchange=()=>{try{localStorage.setItem('sw-voice-provider',voiceProvider());}catch{}stopRealtime('Proveedor cambiado. Confirmá sus condiciones antes de conectar.');$('realtime-key').value='';realtimeConsent=false;$('realtime-consent').checked=false;realtimeConfigured=!!realtimeProviders[voiceProvider()];updateVoiceProviderNote();refreshVoiceStorage().catch(e=>notice(e.message,true));renderRealtime();};
try{const provider=localStorage.getItem('sw-voice-provider');if(['openai','gemini'].includes(provider))$('realtime-provider').value=provider;}catch{}
api('/api/realtime').then(result=>{realtimeProviders=result.providers;realtimeConfigured=!!realtimeProviders[voiceProvider()];renderRealtime();}).catch(error=>realtimeStatus(error.message));

$('voice-mode').value=storedAppearance('sw-voice-mode','chat')==='controls'?'controls':'chat';
$('voice-mode').onchange=()=>{stopRealtime('Modo de voz cambiado. Pulsá el micrófono para conectar.');try{localStorage.setItem('sw-voice-mode',$('voice-mode').value);}catch{}};
