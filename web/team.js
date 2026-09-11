"use strict";
const teamModes=['diagnosis','impact','draft','proposal','summary','translate','panel'];
const readerNames={impatient:'Impaciente',literary:'Voz y estilo',emotional:'Personajes y emoción',analytical:'Causalidad y pistas'};
const teamSection=document.createElement('dialog');teamSection.id='team-settings';
teamSection.setAttribute('aria-labelledby','team-title');
teamSection.innerHTML='<div class="dialog-heading"><h2 id="team-title">Múltiples agentes · experimental</h2><button id="team-close" class="secondary">Volver al chat</button></div><p>Puede consumir bastante más cuota que una conversación con un único agente. El principal reparte tareas, hasta tres colaboradores trabajan simultáneamente y el principal integra sus aportes. No garantiza ahorro ni mayor velocidad.</p><p>El principal usa el modelo y esfuerzo del chat. Elegí los de cada colaborador; se guardan por proyecto. No se aprueba ni modifica el manuscrito automáticamente.</p><label for="team-count">Máximo de colaboradores por mensaje</label><select id="team-count"><option value="1">1</option><option value="2" selected>2</option><option value="3">3</option></select><div id="team-workers"></div><fieldset id="team-readers"><legend>Perfiles del panel ciego, asignados a los colaboradores en este orden</legend>'+Object.entries(readerNames).map(([key,label])=>'<label class="check-row"><input type="checkbox" value="'+key+'"><span>'+label+'</span></label>').join('')+'</fieldset><p>El panel recibe solo los manuscritos y traducciones seleccionados, sin sinopsis, canon, conversación ni opiniones de otros lectores. Son lectores simulados.</p><p id="team-config-status" role="status"></p><button id="team-save" class="primary">Guardar configuración del equipo</button><p>No se sustituyen modelos no disponibles ni se permite crear más agentes. Detener cancela todo el equipo.</p>';
document.body.append(teamSection);
const teamToggle=document.createElement('label');teamToggle.className='team-toggle';teamToggle.innerHTML='<input id="team-enabled" type="checkbox" aria-describedby="team-warning"><span>Utilizar múltiples agentes simultáneos</span>';
document.querySelector('.composer-options').append(teamToggle);
const teamConfigure=document.createElement('button');teamConfigure.id='team-configure';teamConfigure.className='quiet';teamConfigure.textContent='Configurar equipo';teamConfigure.hidden=true;
document.querySelector('.composer-options').append(teamConfigure);
const teamWarning=document.createElement('p');teamWarning.id='team-warning';teamWarning.className='team-warning';teamWarning.hidden=true;teamWarning.setAttribute('role','status');document.querySelector('.composer').append(teamWarning);
let teamFormKey='';
function workerID(kind,index){return 'team-'+kind+(index?'-'+index:'');}
function teamEfforts(index,preferred){
  const model=(accountState.models||[]).find(m=>m.model===$(workerID('model',index)).value),choices=model?.supportedReasoningEfforts||[],select=$(workerID('effort',index));
  select.replaceChildren(...choices.map(e=>new Option(effortLabels[e.reasoningEffort]||e.reasoningEffort,e.reasoningEffort)));
  if(preferred&&!choices.some(e=>e.reasoningEffort===preferred))select.add(new Option(preferred+' · no disponible',preferred));
  select.value=preferred||model?.defaultReasoningEffort||'';
}
function teamWorkers(){return [...$('team-workers').children].map((_,i)=>({model:$(workerID('model',i)).value,effort:$(workerID('effort',i)).value}));}
function renderTeamWorkers(workers){
  $('team-workers').replaceChildren();
  for(let i=0;i<Number($('team-count').value);i++){
    const worker=workers[i]||workers[0]||{model:'gpt-5.6-luna',effort:'max'},box=document.createElement('fieldset');
    box.innerHTML=`<legend>Colaborador ${i+1}</legend><label for="${workerID('model',i)}">Modelo</label><select id="${workerID('model',i)}"></select><label for="${workerID('effort',i)}">Esfuerzo</label><select id="${workerID('effort',i)}"></select>`;
    $('team-workers').append(box);const select=$(workerID('model',i)),models=accountState.models||[];
    select.replaceChildren(...models.map(m=>new Option(m.displayName,m.model)));
    if(!models.some(m=>m.model===worker.model))select.add(new Option(worker.model+' · no disponible',worker.model));
    select.value=worker.model;teamEfforts(i,worker.effort);select.onchange=()=>teamEfforts(i);
  }
}
function renderTeam(){
  const preferences=state?.team_preferences,models=accountState.models||[],external=selectedEngine()!=='codex';
  const key=JSON.stringify([state?.id,preferences,models]);
  if(key!==teamFormKey){
    teamFormKey=key;$('team-count').value=preferences?.max_agents||2;
    renderTeamWorkers(preferences?.workers||Array(Number($('team-count').value)).fill(preferences||{model:'gpt-5.6-luna',effort:'max'}));
    for(const input of $('team-readers').querySelectorAll('input'))input.checked=(preferences?.readers||['impatient','literary']).includes(input.value);
  }
  const allowed=!!state&&!external&&teamModes.includes($('mode').value);
  teamToggle.hidden=!allowed;$('team-enabled').disabled=!!busy()||!models.length;
  if(!allowed)$('team-enabled').checked=false;
  teamConfigure.hidden=!allowed||!$('team-enabled').checked;
  $('team-save').disabled=!state||!!busy()||!models.length||external;
  $('team-config-status').textContent=preferences?'Configuración guardada por proyecto.':'Elegí modelos disponibles y guardá antes de enviar.';
  teamWarning.hidden=!$('team-enabled').checked;
  teamWarning.textContent='Experimental · utilizar múltiples agentes puede consumir bastante más cuota. Se activa solo para este mensaje.';
}
function openTeam(){renderTeam();showDialog(teamSection);$('team-count').focus();}
teamConfigure.onclick=openTeam;
$('team-close').onclick=()=>teamSection.close();
teamSection.addEventListener('close',()=>{if(!state?.team_preferences)$('team-enabled').checked=false;renderTeam();$('team-enabled').focus();});
$('team-count').onchange=()=>renderTeamWorkers(teamWorkers());
$('team-enabled').onchange=()=>{renderTeam();if($('team-enabled').checked)openTeam();};
$('team-save').onclick=action(async()=>{
  const project=state.id,workers=teamWorkers(),preferences={...workers[0],workers,max_agents:workers.length,readers:[...$('team-readers').querySelectorAll('input:checked')].map(e=>e.value)};
  if($('mode').value==='panel'&&preferences.readers.length>workers.length)throw Error('Elegí tantos colaboradores como perfiles del panel.');
  const updated=await api('/api/project/team',{project,preferences});
  if(state?.id===project){state.team_preferences=updated.team_preferences;renderTeam();teamSection.close();}
});
function teamHTML(run){
  if(!run.team)return '';
  const workers=run.team_workers||[],completed=workers.filter(w=>w.status==='completed').length,key='team-'+run.id;
  return '<details class="team-results" data-output="'+escapeHTML(key)+'" '+(outputPreference(key).open?'open':'')+'><summary>Equipo · '+completed+'/'+workers.length+' aportes listos</summary><p>'+escapeHTML(run.mode==='panel'?'Lecturas independientes de manuscritos/traducciones; sin opiniones previas ni contexto del autor.':'Aportes provisionales, consolidados por el principal.')+'</p>'+workers.map((w,index)=>'<details data-output="'+escapeHTML(key+'-'+index)+'" '+(outputPreference(key+'-'+index).open?'open':'')+'><summary>'+escapeHTML(w.title)+' · '+escapeHTML(w.model||run.team.model)+' · '+escapeHTML(w.effort||run.team.effort)+' · '+escapeHTML(labels[w.status]||w.status)+'</summary><p>'+escapeHTML(w.assignment)+'</p><div class="run-text markdown">'+markdown(w.text||'Sin resultado todavía.')+'</div></details>').join('')+'</details>';
}
renderTeam();
