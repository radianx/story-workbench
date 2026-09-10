'use strict';
const engineLabels={codex:'Codex · ChatGPT',openai:'OpenAI API',gemini:'Google Gemini',anthropic:'Anthropic',deepseek:'DeepSeek',kimi:'Kimi',local:'Servidor local'};
let engineStorage={available:false,stored:{}},engineKeys={},engineSettingsProject=null;
const selectedEngine=()=>state?.engine?.provider||'codex';
function renderEngine(){
  const provider=selectedEngine(),external=provider!=='codex';
  $('connection').textContent=engineLabels[provider]+(external?' · experimental':'');
  $('engine-current').textContent=state?`Motor del proyecto: ${engineLabels[provider]}${external?' · experimental':''}`:'Elegí un proyecto para asignar su motor.';
  $('engine-open').disabled=!!busy();
  $('ai-options').hidden=external;
  $('chat-ai-settings').hidden=external;$('chat-engine').hidden=!external;
  $('chat-engine').textContent='Modelo: '+(state?.engine?.model||engineLabels[provider]);$('chat-engine').disabled=!!busy();
  document.querySelector('.skill-check').hidden=external;
  $('engine-context-note').textContent=external?'Se envían petición, fuentes marcadas, decisiones e historial compatible al proveedor elegido. API con condiciones y facturación propias; no hay fallback.':'Las tareas editoriales usan tu sesión ChatGPT mediante Codex. No hay fallback de pago.';
}
async function engineReady(){
  if(selectedEngine()==='codex')return ensureAccount();
  engineKeys=await api('/api/engines');
  if(selectedEngine()==='local'||engineKeys[selectedEngine()])return true;
  await openEngineSettings();notice('Ingresá la clave del proveedor editorial para continuar.',true);return false;
}
function renderEngineFields(){
  const provider=$('engine-provider').value,external=provider!=='codex';
  $('engine-api-fields').hidden=!external;$('engine-local-label').hidden=provider!=='local';
  $('engine-model').required=external;$('engine-key').value='';
  $('engine-remember').disabled=!engineStorage.available;$('engine-remember').checked=!!engineStorage.stored[provider];
  $('engine-key-status').textContent=engineKeys[provider]?(engineStorage.stored[provider]?'Clave guardada cifrada en este equipo.':'Clave disponible en memoria.'):'Sin clave configurada.';
  $('engine-storage-note').textContent=engineStorage.reason||'';
  $('engine-key-label').firstChild.textContent=provider==='local'?'Clave del servidor (opcional)':'Clave API';
  $('engine-save').textContent=state?'Usar este motor en el proyecto':'Guardar clave para después';
  $('engine-save').disabled=!state&&!external;
}
async function openEngineSettings(){
  [engineStorage,engineKeys]=await Promise.all([api('/api/engine-storage'),api('/api/engines')]);
  engineSettingsProject=state?.id||null;
  const engine=state?.engine||{provider:'codex'};
  $('engine-provider').value=engine.provider;$('engine-model').value=engine.model||'';
  $('engine-endpoint').value=engine.endpoint||'http://127.0.0.1:11434/v1';
  $('engine-consent').checked=false;renderEngineFields();showDialog($('engine-dialog'));
}
$('engine-open').onclick=action(openEngineSettings);
$('setup-engine').onclick=action(openEngineSettings);
$('engine-provider').onchange=()=>{$('engine-model').value='';$('engine-consent').checked=false;renderEngineFields();};
$('engine-close').onclick=()=>$('engine-dialog').close();
$('engine-dialog').addEventListener('close',()=>{$('engine-key').value='';});
$('engine-forget').onclick=action(async()=>{engineKeys=await api('/api/engine/key',{provider:$('engine-provider').value,key:''});engineStorage=await api('/api/engine-storage');renderEngineFields();});
$('engine-form').onsubmit=action(async event=>{
  event.preventDefault();
  if((state?.id||null)!==engineSettingsProject)throw new Error('El proyecto cambió. Volvé a abrir la configuración del motor.');
  const provider=$('engine-provider').value,engine={provider};
  if(provider!=='codex'){
    if(!$('engine-consent').checked)throw new Error('Confirmá el uso del proveedor elegido.');
    engine.model=$('engine-model').value.trim();if(provider==='local')engine.endpoint=$('engine-endpoint').value.trim();
    const key=$('engine-key').value.trim();$('engine-key').value='';
    if(key)engineKeys=await api('/api/engine/key',{provider,key,remember:$('engine-remember').checked});
    else if(engineKeys[provider]&&engineStorage.available)await api('/api/engine-storage',{provider,remember:$('engine-remember').checked});
    if(provider!=='local'&&!engineKeys[provider])throw new Error('Ingresá una clave API para ese proveedor.');
  }
  if(state){
    const updated=await api('/api/project/engine',{project:state.id,engine});state.engine=updated.engine;state.thread=null;state.context_key=null;
    renderEngine();renderAISettings();updateRealtime();
  }
  $('engine-dialog').close();notice(state?'Motor guardado. Se usará en la próxima tarea.':'Clave preparada. Elegí el motor al abrir tu proyecto.');
});
