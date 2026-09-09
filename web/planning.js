'use strict';
const stageLabels = {planned:'Por escribir', drafting:'En borrador', revise:'Por revisar', reviewed:'Revisado'};
const stageOf = doc => doc.stage || (doc.content.trim()?'drafting':'planned');
const manuscripts = () => state.documents.filter(d=>d.role==='manuscrito');
function renderBookProgress() {
  if(!state)return;
  const docs=manuscripts(), words=docs.reduce((n,d)=>n+wordCount(d.content),0), reviewed=docs.filter(d=>stageOf(d)==='reviewed').length;
  const goal=state.word_goal||0;
  const html=`<strong>${words.toLocaleString('es')} palabras guardadas${goal?` / ${goal.toLocaleString('es')}`:''}</strong>${goal?`<progress max="${goal}" value="${Math.min(words,goal)}" aria-label="Meta de palabras del libro"></progress>`:''}<small>${reviewed} de ${docs.length} capítulos o escenas revisados</small><progress max="${docs.length||1}" value="${reviewed}" aria-label="Documentos de manuscrito revisados"></progress>`;
  $('book-progress').innerHTML=$('plan-progress').innerHTML=html;
}
function renderPlan() {
  const all=manuscripts(), filter=$('plan-filter').value;
  $('plan-cards').innerHTML=all.map((d,i)=>({d,i})).filter(({d})=>filter==='all'||stageOf(d)===filter).map(({d,i})=>`<form class="plan-card" data-scene="${d.id}" data-hash="${d.hash}"><div class="plan-card-heading"><strong>${i+1}. ${escapeHTML(d.name.replace(/\.md$/i,''))}</strong><span>${wordCount(d.content)} palabras</span></div><label>Sinopsis provisional<textarea name="synopsis" maxlength="4000" rows="3">${escapeHTML(d.synopsis||'')}</textarea></label><div class="plan-fields"><label>Punto de vista<input name="pov" maxlength="200" value="${escapeHTML(d.pov||'')}" placeholder="Quién vive esta escena"></label><label>Estado<select name="stage">${Object.entries(stageLabels).map(([k,v])=>`<option value="${k}" ${stageOf(d)===k?'selected':''}>${v}</option>`).join('')}</select></label></div><div class="plan-actions"><button type="button" data-move="-1" ${i===0?'disabled':''} aria-label="Subir ${escapeHTML(d.name)}">↑</button><button type="button" data-move="1" ${i===all.length-1?'disabled':''} aria-label="Bajar ${escapeHTML(d.name)}">↓</button><button type="button" data-open-scene>Editar texto</button><button type="button" data-draft-scene>Preparar con IA</button><button type="submit" class="secondary">Guardar ficha</button></div><span class="scene-feedback" role="status"></span></form>`).join('') || '<p class="assistant-empty">No hay documentos en este estado. Agregá un capítulo o escena para empezar.</p>';
  renderBookProgress();
}
function checkPlanEdits() {
  if($('plan-dialog').dataset.dirty==='true')throw new Error('Guardá las fichas pendientes antes de continuar.');
}
$('plan-open').onclick=()=>{if(!state)return;$('goal-form').dataset.dirty='false';$('word-goal').value=state.word_goal||0;$('plan-filter').value='all';$('plan-dialog').dataset.dirty='false';renderPlan();$('plan-dialog').showModal();};
function closePlan(event) {
  if($('plan-dialog').dataset.dirty==='true' && !confirm('¿Cerrar sin guardar los cambios de las fichas o la meta?')){event?.preventDefault();return;}
  $('plan-dialog').close();
}
$('plan-close').onclick=closePlan; $('plan-dialog').oncancel=closePlan;
$('plan-dialog').oninput=e=>{if(e.target.closest('form')){$('plan-dialog').dataset.dirty='true';e.target.closest('form').dataset.dirty='true';}};
function updatePlanDirty(){ $('plan-dialog').dataset.dirty=String(!!$('plan-dialog').querySelector('form[data-dirty="true"]')); }
$('plan-filter').onchange=action(()=>{try{checkPlanEdits();renderPlan();}catch(e){$('plan-filter').value='all';throw e;}});
$('goal-form').onsubmit=action(async e=>{e.preventDefault();const updated=await api('/api/project/goal',{project:state.id,goal:Number($('word-goal').value)});state=updated;$('goal-form').dataset.dirty='false';updatePlanDirty();renderBookProgress();notice('Meta guardada.');});
$('plan-cards').onsubmit=action(async e=>{
  e.preventDefault();const form=e.target, fields=new FormData(form);
  if(dirty && current?.id===form.dataset.scene && fields.get('stage')==='reviewed')throw new Error('Guardá primero el texto del editor para marcarlo como revisado.');
  state=await api('/api/document/planning',{project:state.id,document:form.dataset.scene,planning:{synopsis:fields.get('synopsis'),pov:fields.get('pov'),stage:fields.get('stage'),hash:form.dataset.hash}});
  form.dataset.dirty='false';updatePlanDirty();form.querySelector('.scene-feedback').textContent='Ficha guardada.';renderBookProgress();renderDocuments();
});
$('plan-cards').onclick=action(async e=>{
  const button=e.target.closest('button[type="button"]');if(!button)return;checkPlanEdits();
  const form=button.closest('form'), id=form.dataset.scene;
  if(button.dataset.move){const order=manuscripts().map(d=>d.id), index=order.indexOf(id), to=index+Number(button.dataset.move);[order[index],order[to]]=[order[to],order[index]];state=await api('/api/project/order',{project:state.id,order});renderPlan();renderDocuments();return;}
  if(dirty)throw new Error('Guardá el texto del editor antes de cambiar de documento.');
  $('plan-dialog').close();openDocument(id);view='edit';renderView();
  if(button.hasAttribute('data-draft-scene')){
    const doc=state.documents.find(d=>d.id===id);$('mode').value='draft';setTaskMode();showPanel('conversation');
    $('prompt').value=`Ayudame a preparar un borrador provisional para «${doc.name}». Sinopsis provisional: ${doc.synopsis||'por definir'}. Punto de vista: ${doc.pov||'por definir'}. Usá las fuentes seleccionadas y las decisiones aprobadas; preguntá por un vacío esencial si falta. El resultado se guardará aparte cuando yo lo elija.`;
    savePromptDraft();$('prompt').focus();notice('Petición preparada. Revisá las fuentes y enviá cuando quieras.');
  }
});
$('scene-add').onclick=action(async()=>{checkPlanEdits();const doc=await api('/api/document/add',{project:state.id,name:`Escena ${manuscripts().length+1}.md`,role:'manuscrito',content:''});state=await api(`/api/projects/${state.id}`);renderPlan();renderDocuments();$('plan-cards').querySelector(`[data-scene="${doc.id}"] textarea`)?.focus();});
for(const [id,format] of [['book-markdown','md'],['book-docx','docx']]) $(id).onclick=action(async()=>{checkPlanEdits();if(dirty)throw new Error('Guardá el texto antes de exportar el libro.');download(await api(`/api/projects/${state.id}/book.${format}`),`libro.${format}`);});
// Plantillas propias de la app; no son una copia de build-novel ni hechos aprobados.
const templates = {
  character:{role:'plan',text:'## Deseo y necesidad\n\nPor definir.\n\n## Conflicto y costo de decidir\n\nPor definir.\n\n## Voz, gestos y relaciones\n\nPor definir.\n\n## Arco: elección y consecuencia\n\nPor definir.\n\n## Hechos aprobados y preguntas abiertas\n\nSeparar con claridad.'},
  world:{role:'plan',text:'## Lugar y experiencia sensorial\n\nPor definir.\n\n## Reglas, límites y costo\n\nPor definir.\n\n## Quién tiene poder y quién paga\n\nPor definir.\n\n## Efectos sobre la historia\n\nPor definir.\n\n## Hechos aprobados y preguntas abiertas\n\nSeparar con claridad.'},
  voice:{role:'estilo',text:'## Perspectiva y tiempo verbal\n\nPor definir.\n\n## Registro, ritmo y diálogo\n\nPor definir.\n\n## Qué debe sentir el lector\n\nPor definir.\n\n## Ejemplo de voz aprobado por el autor\n\nAgregar solo texto propio o autorizado.\n\n## Recursos a evitar\n\nPor definir.'},
  outline:{role:'plan',text:'## Premisa y promesa al lector\n\nPor definir.\n\n## Situación inicial y detonante\n\nPor definir.\n\n## Deseo, obstáculos y decisiones\n\nPor definir.\n\n## Giro y consecuencias\n\nPor definir.\n\n## Clímax y cierre\n\nPor definir.\n\n## Vacíos que debemos conversar\n\nPor definir.'}
};
$('template-open').onclick=()=>{$('template-form').reset();if(state.purpose==='rpg')$('template-type').value='rpg_world';$('template-dialog').showModal();$('template-name').focus();};
$('template-cancel').onclick=()=>$('template-dialog').close();
$('template-form').onsubmit=action(async e=>{
  e.preventDefault();if(dirty)throw new Error('Guardá el documento actual antes de crear una ficha.');
  const name=$('template-name').value.trim(), template=templates[$('template-type').value];if(!name)return;
  const button=e.submitter;button.disabled=true;
  try {const doc=await api('/api/document/add',{project:state.id,name:name+'.md',role:template.role,selected:false,content:'# '+name+'\n\nFicha provisional — completar y revisar con el autor.\n\n'+template.text+'\n'});state=await api(`/api/projects/${state.id}`);$('template-dialog').close();showMaterial();openDocument(doc.id,true);view='edit';renderView();notice('Ficha creada. Seleccionala en la biblioteca cuando quieras compartirla con Codex.');}finally{button.disabled=false;}
});
