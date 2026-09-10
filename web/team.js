'use strict';
const teamModes=['diagnosis','impact','draft','proposal','summary','translate','panel'];
const readerNames={impatient:'Impaciente',literary:'Voz y estilo',emotional:'Personajes y emoción',analytical:'Causalidad y pistas'};
const teamSection=document.createElement('details');teamSection.id='team-settings';
teamSection.innerHTML='<summary>Equipo editorial · experimental</summary><p>El principal usa el modelo y esfuerzo del chat. Los colaboradores usan la selección explícita de aquí. Se guarda por proyecto.</p><label for="team-preset">Preparar una selección</label><select id="team-preset"><option value="">Personalizada</option><option value="gpt-5.6-luna:max">Luna · máximo</option><option value="gpt-5.6-sol:low">Sol · bajo</option><option value="gpt-5.6-sol:medium">Sol · medio</option></select><label for="team-model">Modelo de los colaboradores</label><select id="team-model"></select><label for="team-effort">Esfuerzo de los colaboradores</label><select id="team-effort"></select><label for="team-count">Máximo de colaboradores por mensaje</label><select id="team-count"><option value="1">1</option><option value="2" selected>2</option><option value="3">3</option></select><fieldset id="team-readers"><legend>Perfiles para el panel ciego</legend>'+Object.entries(readerNames).map(([key,label])=>'<label class="check-row"><input type="checkbox" value="'+key+'" '+(['impatient','literary'].includes(key)?'checked':'')+'><span>'+label+'</span></label>').join('')+'</fieldset><p>El panel recibe solo manuscritos y traducciones marcados, en su orden, sin sinopsis, canon, conversación, objetivo del autor ni opiniones de otros lectores. Son lectores simulados; no reemplazan lectores humanos.</p><p id="team-config-status" role="status"></p><button id="team-save" class="secondary">Guardar configuración del equipo</button><p>No se sustituirá automáticamente un modelo no disponible. No se permite que los colaboradores creen más agentes.</p>';
$('settings-model').append(teamSection);
const teamToggle=document.createElement('label');teamToggle.className='team-toggle';teamToggle.innerHTML='<input id="team-enabled" type="checkbox" aria-describedby="team-warning"><span>Usar equipo</span>';
document.querySelector('.composer-options').append(teamToggle);
const teamConfigure=document.createElement('button');teamConfigure.id='team-configure';teamConfigure.className='quiet';teamConfigure.textContent='Configurar equipo';teamConfigure.onclick=()=>{openSettings();teamSection.open=true;teamSection.scrollIntoView({block:'nearest'});};
document.querySelector('.composer-options').append(teamConfigure);
const teamWarning=document.createElement('p');teamWarning.id='team-warning';teamWarning.className='team-warning';teamWarning.hidden=true;teamWarning.setAttribute('role','status');document.querySelector('.composer').append(teamWarning);
let teamFormKey='';
function teamEfforts(preferred){
  const model=(accountState.models||[]).find(m=>m.model===$('team-model').value),choices=model?.supportedReasoningEfforts||[];
  $('team-effort').replaceChildren(...choices.map(e=>new Option(effortLabels[e.reasoningEffort]||e.reasoningEffort,e.reasoningEffort)));
  if(preferred&&!choices.some(e=>e.reasoningEffort===preferred))$('team-effort').add(new Option(preferred+' · no disponible',preferred));
  $('team-effort').value=preferred||model?.defaultReasoningEffort||'';
}
function renderTeam(){
  if(!$('team-enabled'))return;
  const preferences=state?.team_preferences,models=accountState.models||[],external=selectedEngine()!=='codex';
  const key=JSON.stringify([state?.id,preferences,models]);
  if(key!==teamFormKey){
    teamFormKey=key;const model=preferences?.model||'gpt-5.6-luna';
    $('team-model').replaceChildren(...models.map(m=>new Option(m.displayName,m.model)));
    if(!models.some(m=>m.model===model))$('team-model').add(new Option(model+' · no disponible',model));
    $('team-model').value=model;teamEfforts(preferences?.effort||'max');$('team-count').value=preferences?.max_agents||2;
    for(const input of $('team-readers').querySelectorAll('input'))input.checked=(preferences?.readers||['impatient','literary']).includes(input.value);
    $('team-preset').value='';
  }
  $('team-settings').hidden=external;$('team-configure').hidden=external;
  $('team-save').disabled=!state||!!busy()||!models.length||external;
  const allowed=!!state&&!external&&teamModes.includes($('mode').value);
  teamToggle.hidden=!allowed;$('team-enabled').disabled=!preferences||!!busy();
  if(!allowed||!preferences)$('team-enabled').checked=false;
  $('team-config-status').textContent=preferences?`Guardado: ${preferences.model} · ${effortLabels[preferences.effort]||preferences.effort} · hasta ${preferences.max_agents} colaboradores.`:'Guardá un modelo y esfuerzo disponibles antes de activar el equipo.';
  teamWarning.hidden=!$('team-enabled').checked;
  if(!teamWarning.hidden){const panel=$('mode').value==='panel',count=panel?preferences.readers.length:preferences.max_agents;teamWarning.textContent=`Este mensaje usará hasta ${count} colaboradores (${preferences.model}, ${effortLabels[preferences.effort]||preferences.effort}) y ${panel?1:2} turnos del principal. Puede consumir bastante más cuota que continuar con un solo agente, aun usando modelos más livianos. No es un presupuesto de tokens ni una garantía de ahorro. Detener cancela todo el equipo.`;}
}
$('team-model').onchange=()=>{teamEfforts();$('team-preset').value='';};
$('team-preset').onchange=()=>{
  if(!$('team-preset').value)return;const [model,effort]=$('team-preset').value.split(':');
  if(![...$('team-model').options].some(o=>o.value===model))$('team-model').add(new Option(model+' · no disponible',model));
  $('team-model').value=model;teamEfforts(effort);
};
$('team-save').onclick=action(async()=>{
  const project=state.id,preferences={model:$('team-model').value,effort:$('team-effort').value,max_agents:Number($('team-count').value),readers:[...$('team-readers').querySelectorAll('input:checked')].map(e=>e.value)};
  const updated=await api('/api/project/team',{project,preferences});if(state?.id===project){state.team_preferences=updated.team_preferences;renderTeam();}notice('Equipo guardado. Se activa por mensaje con Usar equipo, fuera de la entrevista.');
});
$('team-enabled').onchange=renderTeam;
function teamHTML(run){
  if(!run.team)return '';
  const workers=run.team_workers||[],completed=workers.filter(w=>w.status==='completed').length,key='team-'+run.id;
  return '<details class="team-results" data-output="'+escapeHTML(key)+'" '+(outputPreference(key).open?'open':'')+'><summary>Equipo · '+completed+'/'+workers.length+' aportes listos · '+escapeHTML(run.team.model)+' · '+escapeHTML(run.team.effort)+'</summary><p>'+escapeHTML(run.mode==='panel'?'Lecturas independientes de manuscritos/traducciones; sin opiniones previas ni contexto del autor.':'Aportes provisionales, consolidados por el principal.')+'</p>'+workers.map((w,index)=>'<details data-output="'+escapeHTML(key+'-'+index)+'" '+(outputPreference(key+'-'+index).open?'open':'')+'><summary>'+escapeHTML(w.title)+' · '+escapeHTML(labels[w.status]||w.status)+'</summary><p>'+escapeHTML(w.assignment)+'</p><div class="run-text">'+escapeHTML(w.text||'Sin resultado todavía.')+'</div></details>').join('')+'</details>';
}
renderTeam();
