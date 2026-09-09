'use strict';
// Mover los controles conserva sus eventos y sus valores; el chat queda libre de setup.
const moveSetting=(selector,section)=>$(section).append(document.querySelector(selector));
moveSetting('.theme-picker','settings-general');moveSetting('#inspire','settings-general');
for(const id of ['purpose','workflow'])moveSetting('#'+id,'settings-project');
for(const label of document.querySelectorAll('.sources .workflow-picker'))label.remove();
for(const id of ['purpose','workflow']){const label=document.createElement('label');label.htmlFor=id;label.textContent=id==='purpose'?'Objetivo':'Forma de trabajo';$(id).before(label);}
moveSetting('.task-guidance','settings-project');
moveSetting('#ai-options','settings-model');$('ai-options').open=true;
moveSetting('.skill-check','settings-model');moveSetting('.composer > .privacy-note','settings-model');
const composer=document.querySelector('.composer'),footer=document.querySelector('.composer-bottom');
footer.prepend($('mode'));
footer.insertBefore($('dictate'),$('cancel'));footer.insertBefore($('dictate-cancel'),$('cancel'));footer.insertBefore($('read-stop'),$('cancel'));
const voiceSession=document.createElement('details');voiceSession.id='voice-session';voiceSession.open=true;
voiceSession.innerHTML='<summary>Conversación de voz</summary>';
for(const id of ['realtime-status','realtime-caption','realtime-actions'])voiceSession.append($(id));
for(const id of ['realtime-stop','realtime-mute'])footer.insertBefore($(id),$('cancel'));
$('runs').after(voiceSession);voiceSession.hidden=true;
moveSetting('#realtime-options','settings-voice');$('realtime-options').open=true;
composer.append($('voice-status'));
moveSetting('.voice-controls','settings-voice');
moveSetting('.composer [data-help=voice]','settings-voice');
const label=document.createElement('label');label.htmlFor='prompt';label.className='message-label';label.textContent='Tu mensaje';$('prompt').before(label);
$('prompt').rows=2;
function openSettings(){$('purpose').disabled=$('workflow').disabled=!state;renderAISettings();$('settings-dialog').showModal();}
$('settings-open').onclick=openSettings;
$('settings-close').onclick=()=>$('settings-dialog').close();
$('settings-dialog').addEventListener('close',()=>{if(!document.querySelector('dialog[open]'))$('prompt').focus();});

// Una paleta por modo: al seguir el sistema se conserva la preferencia de ambos.
const palettes={light:{sage:'Original · salvia',sky:'Blanco · celeste',cream:'Blanco · crema / amarillo',pink:'Blanco · rosado'},dark:{sage:'Original · salvia',violet:'Negro · violeta',red:'Negro · rojo',blue:'Negro · azul'}};
for(const mode of ['light','dark']){
  const label=document.createElement('label');label.textContent=mode==='light'?'Paleta clara':'Paleta oscura';
  const select=document.createElement('select');select.id='palette-'+mode;
  for(const [value,text] of Object.entries(palettes[mode]))select.add(new Option(text,value));
  label.append(select);$('settings-general').insertBefore(label,$('inspire'));
  select.onchange=()=>{document.documentElement.dataset[mode+'Palette']=select.value;try{localStorage.setItem('sw-palette-'+mode,select.value);}catch{notice('La paleta se aplicó, pero no se pudo recordar.',true);}};
}
function restorePalettes(){for(const mode of ['light','dark']){let value;try{value=localStorage.getItem('sw-palette-'+mode);}catch{}value=Object.hasOwn(palettes[mode],value)?value:'sage';$('palette-'+mode).value=value;document.documentElement.dataset[mode+'Palette']=value;}}
restorePalettes();window.addEventListener('storage',e=>{if(!e.key||e.key.startsWith('sw-palette-'))restorePalettes();});
new ResizeObserver(()=>document.documentElement.style.setProperty('--topbar-height',document.querySelector('.topbar').offsetHeight+'px')).observe(document.querySelector('.topbar'));
