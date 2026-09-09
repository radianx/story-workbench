'use strict';
let realtime=null, realtimeConfigured=false, realtimeConsent=false, realtimeProviders={};
const realtimeBusy=()=>!!realtime;
const realtimeSignature=()=>JSON.stringify([state.id,state.purpose,state.translation_config,state.documents.filter(d=>d.selected).map(d=>[d.id,d.hash])]);
const voiceProvider=()=>$('realtime-provider').value;
function realtimeStatus(message){$('realtime-status').textContent=message;}
function renderRealtime(){
  $('realtime-start').hidden=!$('realtime-enabled').checked||!!realtime;
  $('realtime-global-stop').hidden=!realtime;
  $('realtime-stop').hidden=!realtime;$('realtime-mute').hidden=!realtime?.stream;
  $('realtime-start').disabled=!state||!realtimeConfigured||!realtimeConsent;
  renderVoice();
}
function stopRealtime(message='Conversación terminada. Micrófono cerrado.'){
  const session=realtime;realtime=null;
  if(session){if(session.provider==='gemini')closeGeminiVoice(session);clearTimeout(session.timeout);clearInterval(session.timer);session.stream?.getTracks().forEach(t=>t.stop());session.channel?.close();session.pc?.close();session.audio?.pause();if(session.audio)session.audio.srcObject=null;}
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
    if(['conversation','proposals','decisions'].includes(target))showPanel(target);
    else if(target==='help')openHelp();
    else if(['translation','plan','book'].includes(target)){
      const button=$(target+'-open');if(button.hidden||button.disabled)throw new Error('Sección no disponible en este modo.');
      if(document.querySelector('dialog[open]'))throw new Error('Cerrá el diálogo actual antes de abrir otro.');button.click();
    }else throw new Error('Sección no permitida.');
    return {visible:target};
  }
  if(operation==='set_theme'){
    if(!['system','light','dark'].includes(target))throw new Error('Tema inválido.');
    $('theme').value=target;$('theme').onchange();return {theme:target};
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
  if(dirty)throw new Error('Guardá primero los cambios del documento; Codex recibe la versión guardada.');
  if(busy())throw new Error('Ya hay una tarea en curso.');
  if(!await ensureAccount())throw new Error('Conectá tu cuenta ChatGPT para lanzar tareas de Codex.');
  if(realtime!==session||state.id!==session.project||session.signature!==realtimeSignature())throw new Error('La sesión cambió antes del envío.');
  if(session.cancelled?.has(session.currentCall))throw new Error('La petición oral fue interrumpida antes del envío.');
  const run=await api('/api/run',{project:session.project,mode,prompt:text,skill:$('skill').checked});
  if(realtime===session){showPanel('conversation');await poll();}
  return {started:true,run:run.id,next:'El resultado quedará en la conversación de Codex. Consultá get_context para leerlo cuando termine; no está aprobado.'};
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
  if(data.type==='error'){stopRealtime('La sesión de voz informó un error. Revisá conexión y cuota antes de reconectar.');return;}
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
async function startRealtime(){
  if(realtime||!state)return;
  if(!realtimeConfigured||!realtimeConsent||!$('realtime-enabled').checked)throw new Error('Configurá la clave y aceptá el uso de la API antes de conectar.');
  await cancelVoice();
  const session={provider:voiceProvider(),project:state.id,signature:realtimeSignature(),actions:$('realtime-allow-actions').checked,seen:new Set(),queue:Promise.resolve()};
  realtime=session;realtimeStatus(session.provider==='gemini'?'Conectando Gemini Live…':'Conectando gpt-realtime…');renderRealtime();
  session.timeout=setTimeout(()=>{if(realtime===session)stopRealtime('La conexión tardó demasiado. Micrófono cerrado.');},45000);
  try{
    session.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true},video:false});
    if(realtime!==session){session.stream.getTracks().forEach(t=>t.stop());return;}
    if(session.provider==='gemini'){await startGeminiVoice(session);return;}
    session.pc=new RTCPeerConnection();session.audio=new Audio();session.audio.autoplay=true;
    session.pc.ontrack=e=>{if(realtime===session){session.audio.srcObject=e.streams[0];session.audio.play().catch(()=>{if(realtime===session)stopRealtime('No se pudo reproducir la voz. Volvé a conectar.');});}};
    session.pc.onconnectionstatechange=()=>{if(realtime===session&&['failed','disconnected','closed'].includes(session.pc.connectionState))stopRealtime('Conexión de voz cerrada. Podés reconectar manualmente.');};
    session.stream.getTracks().forEach(track=>session.pc.addTrack(track,session.stream));
    session.channel=session.pc.createDataChannel('oai-events');
    session.channel.onmessage=event=>{session.queue=session.queue.then(()=>realtimeEvent(session,event)).catch(()=>{if(realtime===session)stopRealtime('Respuesta de voz inválida. Micrófono cerrado.');});};
    session.channel.onclose=()=>{if(realtime===session)stopRealtime('El servicio cerró la conversación. Micrófono cerrado.');};
    session.channel.onopen=()=>realtimeConnected(session);
    renderRealtime();const offer=await session.pc.createOffer();
    if(realtime!==session)return;
    await session.pc.setLocalDescription(offer);
    const answer=await api('/api/realtime/connect',{project:session.project,sdp:offer.sdp,consent:true,actions:session.actions});
    if(realtime!==session)return;
    await session.pc.setRemoteDescription({type:'answer',sdp:answer.sdp});
  }catch(error){if(realtime===session)stopRealtime(error.name==='NotAllowedError'?'Micrófono no autorizado. Podés seguir escribiendo.':error.message);}
}
$('realtime-enabled').onchange=()=>{
  if(!$('realtime-enabled').checked)stopRealtime('Desactivado. El dictado sigue siendo local.');
  else if(!realtimeConfigured||!realtimeConsent)$('realtime-dialog').showModal();
  renderRealtime();
};
$('realtime-settings').onclick=()=>{$('realtime-dialog').showModal();};
$('realtime-dialog').addEventListener('close',()=>{$('realtime-key').value='';});
$('realtime-close').onclick=()=>{$('realtime-dialog').close();};
$('realtime-consent').onchange=()=>{realtimeConsent=false;stopRealtime('Guardá el consentimiento para volver a conectar.');};
$('realtime-allow-actions').onchange=()=>{stopRealtime('Permisos cambiados. Volvé a conectar para aplicarlos.');};
$('realtime-save').onclick=action(async()=>{
  if(!$('realtime-consent').checked)throw new Error('Confirmá el envío al proveedor y las condiciones de la API antes de habilitarlo.');
  stopRealtime();
  const key=$('realtime-key').value;$('realtime-key').value='';
  if(key){const result=await api('/api/realtime/key',{key,provider:voiceProvider()});realtimeProviders=result.providers;realtimeConfigured=realtimeProviders[voiceProvider()];}
  if(!realtimeConfigured)throw new Error('Falta una clave API. Ingresala en este diálogo.');
  realtimeConsent=true;$('realtime-dialog').close();realtimeStatus('Configurado. Pulsá Conversar por voz para abrir el micrófono y conectar.');renderRealtime();
});
$('realtime-forget').onclick=action(async()=>{
  stopRealtime();const result=await api('/api/realtime/key',{key:'',provider:voiceProvider()});realtimeProviders=result.providers;realtimeConfigured=realtimeProviders[voiceProvider()];
  realtimeConsent=false;$('realtime-consent').checked=false;$('realtime-key').value='';$('realtime-enabled').checked=false;
  realtimeStatus('Clave olvidada. Realtime desactivado.');renderRealtime();
});
$('realtime-start').onclick=action(startRealtime);
$('realtime-stop').onclick=$('realtime-global-stop').onclick=()=>stopRealtime();
$('realtime-mute').onclick=()=>{
  if(!realtime?.stream)return;
  const enabled=!realtime.stream.getAudioTracks()[0]?.enabled;realtime.stream.getAudioTracks().forEach(t=>t.enabled=enabled);
  if(realtime.provider==='gemini'&&!enabled)sendGemini(realtime,{realtimeInput:{audioStreamEnd:true}});
  $('realtime-mute').setAttribute('aria-pressed',String(!enabled));$('realtime-mute').textContent=enabled?'Pausar micrófono':'Reactivar micrófono';
};
$('realtime-provider').onchange=()=>{stopRealtime('Proveedor cambiado. Confirmá sus condiciones antes de conectar.');$('realtime-key').value='';realtimeConsent=false;$('realtime-consent').checked=false;realtimeConfigured=!!realtimeProviders[voiceProvider()];$('realtime-provider-note').textContent=voiceProvider()==='gemini'?'Modelo: gemini-3.1-flash-live-preview. Usa una clave de Google AI Studio. AI Plus y la API son servicios separados; acceso, cuota y posibles cargos dependen del proyecto de la clave. Gemini puede operar la app sin una clave OpenAI. Las tareas editoriales siguen usando Codex con ChatGPT.':'Modelo: gpt-realtime. La API se factura por separado. Esta versión de Codex no admite Realtime con la sesión ChatGPT. No hay cambio automático a pago.';renderRealtime();};
api('/api/realtime').then(result=>{realtimeProviders=result.providers;realtimeConfigured=!!realtimeProviders[voiceProvider()];renderRealtime();}).catch(error=>realtimeStatus(error.message));
