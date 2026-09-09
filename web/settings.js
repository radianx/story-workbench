'use strict';
// Mover los controles conserva sus eventos y sus valores; el chat queda libre de setup.
const moveSetting=(selector,section)=>$(section).append(document.querySelector(selector));
const appearanceControls=document.createElement('div');appearanceControls.id='appearance-controls';$('settings-general').append(appearanceControls);
moveSetting('.theme-picker','appearance-controls');moveSetting('#inspire','settings-general');
for(const id of ['purpose','workflow'])moveSetting('#'+id,'settings-project');
for(const label of document.querySelectorAll('.sources .workflow-picker'))label.remove();
for(const id of ['purpose','workflow']){const label=document.createElement('label');label.htmlFor=id;label.textContent=id==='purpose'?'Objetivo':'Forma de trabajo';$(id).before(label);}
moveSetting('.task-guidance','settings-project');
moveSetting('#ai-options','settings-model');$('ai-options').open=true;
moveSetting('.skill-check','settings-model');moveSetting('.composer > .privacy-note','settings-model');
const composer=document.querySelector('.composer'),footer=document.querySelector('.composer-bottom');
footer.prepend($('mode'));
footer.insertBefore($('dictate'),$('cancel'));footer.insertBefore($('dictate-cancel'),$('cancel'));footer.insertBefore($('read-stop'),$('cancel'));
const autoRead=$('auto-read').closest('label');autoRead.className='auto-read-toggle';
const microphoneControls=document.createElement('span');microphoneControls.className='microphone-controls';$('dictate').before(microphoneControls);microphoneControls.append($('dictate'),autoRead);
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
function openSettings(){$('purpose').disabled=$('workflow').disabled=!state;renderAISettings();renderEngine();showDialog($('settings-dialog'));}
$('settings-open').onclick=openSettings;
$('settings-close').onclick=()=>$('settings-dialog').close();
$('settings-dialog').addEventListener('close',()=>{if(!document.querySelector('dialog[open]'))$('prompt').focus();});

const appearanceNote=document.createElement('p');appearanceNote.className='appearance-note';appearanceNote.textContent='El tema se guarda automáticamente para tu usuario en este equipo. Sistema sigue los cambios de apariencia del equipo.';appearanceControls.append(appearanceNote);
new ResizeObserver(()=>document.documentElement.style.setProperty('--topbar-height',document.querySelector('.topbar').offsetHeight+'px')).observe(document.querySelector('.topbar'));
