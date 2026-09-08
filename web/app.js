'use strict';
const $ = id => document.getElementById(id);
// El navegador sigue el sistema con color-scheme; solo guardamos una elección explícita.
function applyTheme(value) {
  const theme = ['light', 'dark'].includes(value) ? value : 'system';
  document.documentElement.dataset.theme = theme;
  $('theme').value = theme;
}
try { applyTheme(localStorage.getItem('sw-theme')); } catch { applyTheme('system'); }
$('theme').onchange = () => {
  applyTheme($('theme').value);
  try {
    if ($('theme').value === 'system') localStorage.removeItem('sw-theme');
    else localStorage.setItem('sw-theme', $('theme').value);
  } catch { notice('El tema se aplicó, pero el navegador no permitió recordar la elección.', true); }
};
window.addEventListener('storage', event => {
  if (event.key === 'sw-theme' || event.key === null) {
    try { applyTheme(localStorage.getItem('sw-theme')); } catch { applyTheme('system'); }
  }
});
const escapeHTML = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {manuscrito:'Manuscrito',canon:'Canon',estilo:'Voz y estilo',referencia:'Referencia',plan:'Planificación','traducción':'Traducción',accepted:'Aprobada',rejected:'Rechazada',pending:'Pendiente',chat:'Conversación',diagnosis:'Diagnóstico',impact:'Impacto',proposal:'Propuesta',summary:'Resumen',connecting:'Conectando con ChatGPT…',running:'Codex está trabajando…',cancelling:'Deteniendo…',completed:'Completado',interrupted:'Interrumpido',failed:'No completado'};
let token = new URLSearchParams(location.hash.slice(1)).get('token') || sessionStorage.getItem('sw-token') || '';
if (token) sessionStorage.setItem('sw-token', token);
history.replaceState(null, '', '/');
let state = null, current = null, dirty = false, view = 'edit', panel = 'conversation', polling = false, backgroundURL = null;
let stateEpoch = 0;
let noticeTimer, lastRuns = '', lastProposals = '', lastDecisions = '';
const busy = () => state?.runs.findLast(r => ['connecting','running','cancelling'].includes(r.status));
const draftKey = () => `sw-draft-${state.id}-${current.id}`;

function notice(text, error=false) {
  $('notice').textContent = text; $('notice').classList.toggle('error',error); $('notice').hidden = false;
  clearTimeout(noticeTimer); noticeTimer = setTimeout(() => $('notice').hidden = true, error ? 12000 : 4500);
}
async function api(path, data) {
  if(data)stateEpoch++;
  const response = await fetch(path, {method:data ? 'POST':'GET', headers:{Authorization:`Bearer ${token}`, ...(data ? {'Content-Type':'application/json'}:{})}, body:data ? JSON.stringify(data):undefined});
  if(data)stateEpoch++;
  if (!response.ok) {const body = await response.json(); const error = new Error(body.error); error.status = response.status; throw error;}
  return response.headers.get('content-type').includes('application/json') ? response.json() : response.blob();
}
function action(fn) {return async event => {try {await fn(event);} catch(error) {notice(error.message,true);}};}
function confirmLeave() {return !dirty || confirm('Hay cambios sin guardar. Se conserva un borrador en esta pestaña. ¿Querés cambiar de documento?');}
async function refreshProjects() {
  const data = await api('/api/projects');
  $('project').innerHTML = data.projects.map(p=>`<option value="${p.id}">${escapeHTML(p.title)}</option>`).join('');
  if (state) $('project').value = state.id;
  return data.projects;
}
async function openProject(id) {
  if (!confirmLeave()) {$('project').value=state.id; return;}
  state = await api(`/api/projects/${id}`); current = null; dirty=false;
  if(backgroundURL){URL.revokeObjectURL(backgroundURL);backgroundURL=null;$('ambient-image').hidden=true;$('inspire').textContent='◐ Ambiente';}
  sessionStorage.setItem('sw-project',id);
  $('welcome').hidden = true; $('workspace').hidden = false; $('export').disabled = false;
  $('project').value=id; $('project-title').textContent=state.title;
  lastRuns=lastProposals=lastDecisions='';
  renderDocuments(); renderAssistant();
  if(state.documents.length) {const last=sessionStorage.getItem(`sw-doc-${id}`);openDocument(state.documents.some(d=>d.id===last)?last:state.documents[0].id,true);}
  else clearDocument();
}
function clearDocument() {
  current=null; $('editor').value=''; $('doc-title').value=''; $('editor').disabled=true;
  for(const id of ['save','rename','role','download']) $(id).disabled=true;
  $('history').textContent='Todavía no hay documentos.'; updateStats();
}
function renderDocuments() {
  const term=$('search').value.toLocaleLowerCase();
  const docs=state.documents.filter(d=>`${d.name} ${d.content}`.toLocaleLowerCase().includes(term));
  $('documents').innerHTML=docs.map(d=>`<div class="document-item ${d.id===current?.id?'active':''}"><button data-doc="${d.id}"><span class="document-icon" aria-hidden="true">${d.role==='canon'?'◇':d.role==='estilo'?'✧':'≡'}</span><span><strong>${escapeHTML(d.name.replace(/\.md$/i,''))}</strong><small>${labels[d.role]} · ${wordCount(d.content)} palabras</small></span></button><input type="checkbox" data-context="${d.id}" ${d.selected?'checked':''} aria-label="Compartir ${escapeHTML(d.name)} con Codex"></div>`).join('') || '<p class="assistant-empty">No hay documentos que coincidan.</p>';
  $('doc-count').textContent=state.documents.length;
  const selected=state.documents.filter(d=>d.selected), chars=selected.reduce((n,d)=>n+d.content.length,0);
  $('context-count').textContent=`${selected.length} fuente${selected.length===1?'':'s'} seleccionada${selected.length===1?'':'s'}`;
  $('context-size').textContent=`${chars.toLocaleString('es')} / 60.000 caracteres`;
}
function openDocument(id, force=false) {
  if(!force && !confirmLeave()) return;
  current={...state.documents.find(d=>d.id===id)};
  if(!current.id) return clearDocument();
  sessionStorage.setItem(`sw-doc-${state.id}`,current.id);
  $('editor').disabled=false; for(const id of ['save','rename','role','download']) $(id).disabled=false;
  $('doc-title').value=current.name.replace(/\.md$/i,''); $('role').value=current.role;
  $('doc-role-label').textContent=labels[current.role]; $('editor').value=current.content;
  dirty=false; $('conflict').hidden=true;
  const draft=sessionStorage.getItem(draftKey());
  if(draft!==null && draft!==current.content) {$('editor').value=draft; dirty=true; notice('Recuperamos tu borrador de esta pestaña. Revisalo antes de guardar.');}
  renderDocuments(); updateStats(); renderView();
}
function wordCount(text) {return text.trim() ? text.trim().split(/\s+/u).length:0;}
function updateStats() {
  const n=wordCount($('editor').value); $('words').textContent=`${n.toLocaleString('es')} palabras`;
  $('reading').textContent=`${Math.max(1,Math.ceil(n/220))} min de lectura`;
  $('save-state').textContent=dirty?'Borrador sin guardar':'Guardado local';
  $('save').disabled=!current || !dirty;
}
function markdown(text) {
  // Markdown acotado: texto escapado, sin HTML ni recursos externos.
  const inline=s=>escapeHTML(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>');
  return text.split(/\n\s*\n/).map(block=>{
    if(block.startsWith('```')) return `<pre>${escapeHTML(block.replace(/^```[^\n]*\n?/, '').replace(/\n?```$/, ''))}</pre>`;
    return block.split('\n').map(line=>{
      const h=line.match(/^(#{1,3}) (.*)$/); if(h)return `<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`;
      if(line.startsWith('> '))return `<blockquote>${inline(line.slice(2))}</blockquote>`;
      if(/^[-*] /.test(line))return `<div>• ${inline(line.slice(2))}</div>`;
      return `<div>${inline(line)||'<br>'}</div>`;
    }).join('');
  }).map(block=>`<section>${block}</section>`).join('<br>');
}
function renderView() {
  $('editor').hidden=view!=='edit'; $('preview').hidden=view!=='preview'; $('history').hidden=view!=='history';
  document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);b.setAttribute('aria-selected',b.dataset.view===view);});
  if(view==='preview') $('preview').innerHTML=markdown($('editor').value);
  if(view==='history' && current) $('history').innerHTML=current.history.slice().reverse().map(v=>`<div class="history-entry"><div>${escapeHTML(v.reason)}<small>${new Date(v.date*1000).toLocaleString('es')}</small></div><button class="secondary" data-restore="${v.id}">Restaurar</button></div>`).join('') || '<p class="assistant-empty">Cada guardado que cambia el texto conserva la versión anterior aquí.</p>';
}
async function save() {
  if(!current || !dirty)return;
  const documentId=current.id, content=$('editor').value;
  try {
    const saved=await api('/api/document/save',{project:state.id,document:documentId,content,hash:current.hash});
    state.documents=state.documents.map(d=>d.id===saved.id?saved:d);
    current=saved;
    dirty=$('editor').value!==content;
    if(!dirty)sessionStorage.removeItem(draftKey());
    $('conflict').hidden=true; updateStats();renderDocuments();notice('Guardado. La versión anterior está en el historial.');
  } catch(error) {if(error.status===409)$('conflict').hidden=false;throw error;}
}
async function nameDialog(title, value='') {
  $('dialog-title').textContent=title; $('new-name').value=value; $('name-dialog').showModal(); $('new-name').focus();
  return new Promise(resolve=>$('name-dialog').addEventListener('close',()=>resolve($('name-dialog').returnValue==='ok'?$('new-name').value.trim():null),{once:true}));
}
async function createProject(demo=false) {
  if(!confirmLeave())return;
  const title=demo?'El faro · proyecto ficticio':await nameDialog('Dale un nombre a tu historia');
  if(!title)return;
  const project=await api('/api/projects',{title,demo});dirty=false;
  await refreshProjects(); await openProject(project.id);
}
function renderAssistant() {
  const active=busy(); $('cancel').hidden=!active; $('send').disabled=!!active;
  $('connection').textContent=active?labels[active.status]:'Codex · ChatGPT';
  const runsKey=JSON.stringify([state.runs,state.documents.map(d=>d.hash)]);
  if(runsKey!==lastRuns){
    const nearBottom=$('runs').scrollHeight-$('runs').scrollTop-$('runs').clientHeight<100;
    lastRuns=runsKey;
    $('runs').innerHTML=state.runs.map(r=>`<div class="run"><div class="run-prompt">${escapeHTML(r.prompt)}</div><div class="run-label">✧ ${labels[r.mode].toUpperCase()} · ${labels[r.status]||r.status}</div><div class="run-text">${escapeHTML(r.text || (['running','connecting'].includes(r.status)?'Preparando una respuesta…':''))}</div>${r.error?`<div class="run-error">${escapeHTML(r.error)}</div>`:''}<details class="run-sources"><summary>${r.sources.length} fuentes enviadas ${r.skill?'· build-novel':''}</summary>${r.sources.map(s=>`${escapeHTML(s.name)} · ${s.hash.slice(0,8)}${state.documents.find(d=>d.id===s.id)?.hash!==s.hash?' · cambió desde este envío':''}`).join('<br>')}<br>Se enviaron como texto. No afirmamos lectura mediante herramientas.</details>${r.mode==='summary' && r.status==='completed'?`<button class="quiet" data-summary="${r.id}">Guardar resumen como fuente provisional</button>`:''}</div>`).join('') || '<div class="assistant-empty"><div class="empty-symbol">✧</div><h3>Tu historia, con otra mirada.</h3><p>Las fuentes dan contexto.<br>Vos marcás el rumbo.</p><div class="quick-actions"><button data-quick="diagnosis">◈ Encontrar contradicciones</button><button data-quick="impact">↗ ¿Qué cambia si cambio esto?</button><button data-quick="proposal">≋ Afinar un pasaje</button></div></div>';
    if(nearBottom || state.runs.length===1)$('runs').scrollTop=$('runs').scrollHeight;
  }
  const proposalsKey=JSON.stringify(state.proposals);
  $('proposal-count').textContent=state.proposals.filter(p=>p.status==='pending').length;
  if(proposalsKey!==lastProposals){
    lastProposals=proposalsKey;
    $('proposals').innerHTML=state.proposals.slice().reverse().map(p=>`<article class="proposal"><h4>${escapeHTML(state.documents.find(d=>d.id===p.document)?.name||'Documento')}</h4><p>${escapeHTML(p.reason)}</p><small>ANTES</small><pre class="before">${escapeHTML(p.before)}</pre><small>PROPUESTA</small><pre class="after">${escapeHTML(p.after)}</pre><div class="proposal-actions">${p.status==='pending'?`<button class="quiet" data-reject="${p.id}">Rechazar</button><button class="primary" data-accept="${p.id}">Aceptar bloque</button>`:`<span class="tag">${labels[p.status]}</span>`}</div></article>`).join('') || '<p class="assistant-empty">Cuando pidas «Proponer cambios», los bloques aparecerán aquí para revisarlos.</p>';
  }
  const decisionsKey=JSON.stringify(state.decisions);
  if(decisionsKey!==lastDecisions){lastDecisions=decisionsKey;$('decisions').innerHTML=state.decisions.slice().reverse().map(d=>`<div class="decision"><span class="tag">${labels[d.status]}</span><p>${escapeHTML(d.text)}</p><small>${new Date(d.date*1000).toLocaleString('es')}</small></div>`).join('') || '<p class="assistant-empty">Todavía no registraste decisiones.</p>';}
}
function showPanel(name) {
  panel=name; for(const n of ['conversation','proposals','decisions']) $(`${n}-panel`).hidden=n!==name;
  document.querySelectorAll('[data-panel]').forEach(b=>{b.classList.toggle('active',b.dataset.panel===name);b.setAttribute('aria-selected',b.dataset.panel===name);});
}
async function poll() {
  if(!state || polling)return;
  polling=true;
  try {
    const project=state.id, epoch=stateEpoch, incoming=await api(`/api/projects/${project}`);
    if(project!==state?.id || epoch!==stateEpoch)return;
    const wasBusy=!!busy();
    state=incoming;
    if(current){const latest=state.documents.find(d=>d.id===current.id);if(latest && latest.hash!==current.hash)$('conflict').hidden=false;}
    renderAssistant();
    if(wasBusy && !busy()) {renderDocuments();notice(state.runs.at(-1).status==='completed'?'La respuesta está lista.':'La tarea terminó. Revisá su estado.');}
  }catch(error){if(busy())notice(error.message,true);}finally{polling=false;}
}
function download(blob,name) {const url=URL.createObjectURL(blob), link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function downloadDocument(){if(current)download(new Blob([$('editor').value],{type:'text/markdown;charset=utf-8'}),current.name.replace(/\.md$/i,'')+'.md');}

$('demo').onclick=action(()=>createProject(true)); $('blank').onclick=action(()=>createProject()); $('new-project').onclick=action(()=>createProject());
$('project').onchange=action(e=>openProject(e.target.value)); $('search').oninput=renderDocuments;
$('documents').onclick=action(e=>{const b=e.target.closest('[data-doc]');if(b)openDocument(b.dataset.doc);});
$('documents').onchange=action(async e=>{if(!e.target.dataset.context)return;state=await api('/api/document/meta',{project:state.id,document:e.target.dataset.context,selected:e.target.checked});renderDocuments();});
$('new-doc').onclick=action(async()=>{const name=await nameDialog('Un documento nuevo');if(!name)return;const doc=await api('/api/document/add',{project:state.id,name:name+'.md',role:'manuscrito',content:''});state=await api(`/api/projects/${state.id}`);openDocument(doc.id);});
$('import').onclick=()=>$('files').click();
$('files').onchange=action(async e=>{
  for(const file of e.target.files){if(!/\.(md|markdown|txt)$/i.test(file.name))throw new Error('Importá archivos Markdown o TXT.');if(file.size>250000)throw new Error(`${file.name}: máximo 250 KB por documento.`);const bytes=await file.arrayBuffer();const content=new TextDecoder('utf-8',{fatal:true}).decode(bytes);await api('/api/document/add',{project:state.id,name:file.name,role:'referencia',content});}
  state=await api(`/api/projects/${state.id}`);renderDocuments();if(!current && state.documents.length)openDocument(state.documents[0].id,true);e.target.value='';notice('Copias importadas. Asignales un tipo y seleccioná las fuentes para Codex.');
});
$('editor').oninput=()=>{if(!current)return;dirty=$('editor').value!==current.content;try{sessionStorage.setItem(draftKey(),$('editor').value);}catch{notice('No se pudo conservar el borrador de la pestaña. Guardá o descargá tu texto.',true);}updateStats();};
$('save').onclick=action(save);$('download').onclick=downloadDocument;
$('rename').onclick=action(async()=>{if(!current)return;state=await api('/api/document/meta',{project:state.id,document:current.id,name:$('doc-title').value.trim()+'.md'});current.name=state.documents.find(d=>d.id===current.id).name;renderDocuments();notice('Nombre actualizado.');});
$('role').onchange=action(async e=>{if(!current)return;state=await api('/api/document/meta',{project:state.id,document:current.id,role:e.target.value});current.role=e.target.value;$('doc-role-label').textContent=labels[current.role];renderDocuments();});
$('reload').onclick=action(async()=>{if(dirty && !confirm('¿Descartar el borrador y cargar la versión guardada?'))return;sessionStorage.removeItem(draftKey());state=await api(`/api/projects/${state.id}`);openDocument(current.id,true);});
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view;renderView();});
document.querySelectorAll('[data-panel]').forEach(b=>b.onclick=()=>showPanel(b.dataset.panel));
document.querySelectorAll('[data-format]').forEach(b=>b.onclick=()=>{if(!current)return;view='edit';renderView();const e=$('editor'),start=e.selectionStart,end=e.selectionEnd,selected=e.value.slice(start,end),mark=b.dataset.format==='bold'?'**':b.dataset.format==='italic'?'*':'## ';e.setRangeText(mark+selected+(b.dataset.format==='heading'?'':mark),start,end,'select');e.focus();e.dispatchEvent(new Event('input'));});
$('history').onclick=action(async e=>{const b=e.target.closest('[data-restore]');if(!b)return;if(dirty)throw new Error('Guardá o descargá tu borrador antes de restaurar.');if(!confirm('¿Restaurar esta versión? También conservaremos la versión actual.'))return;const doc=await api('/api/document/restore',{project:state.id,document:current.id,version:b.dataset.restore,hash:current.hash});state.documents=state.documents.map(d=>d.id===doc.id?doc:d);sessionStorage.removeItem(draftKey());openDocument(doc.id,true);notice('Versión restaurada.');});
$('runs').onclick=action(async e=>{const b=e.target.closest('[data-quick]');if(b){$('mode').value=b.dataset.quick;$('prompt').value={diagnosis:'Revisá las fuentes seleccionadas y señalá contradicciones con sus pasajes, sin reescribir.',impact:'Si cambiamos este hecho de canon: [describí el cambio], ¿qué más deberíamos revisar?',proposal:'Proponé cambios mínimos y justificados en el manuscrito seleccionado. Conservá voz, tono y canon; separá cada cambio en un bloque.'}[b.dataset.quick];$('prompt').focus();}const s=e.target.closest('[data-summary]');if(s){const r=state.runs.find(r=>r.id===s.dataset.summary);await api('/api/document/add',{project:state.id,name:'Resumen provisional.md',role:'referencia',content:'# Resumen provisional — verificar fuentes\n\n'+r.text+'\n\nFuentes de origen:\n'+r.sources.map(s=>`- ${s.name} (${s.hash})`).join('\n')});state=await api(`/api/projects/${state.id}`);renderDocuments();notice('Resumen guardado como referencia provisional, con sus fuentes.');}});
$('send').onclick=action(async()=>{if(dirty)throw new Error('Guardá el documento antes de enviarlo: Codex recibe la versión guardada.');if(!$('prompt').value.trim())return;await api('/api/run',{project:state.id,mode:$('mode').value,prompt:$('prompt').value.trim(),skill:$('skill').checked});$('prompt').value='';showPanel('conversation');await poll();});
$('cancel').onclick=action(async()=>{const run=busy();if(run){await api('/api/run/cancel',{project:state.id,run:run.id});await poll();}});
$('prompt').onkeydown=e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();$('send').click();}};
$('proposals').onclick=action(async e=>{const b=e.target.closest('[data-accept],[data-reject]');if(!b)return;if(dirty && b.dataset.accept)throw new Error('Guardá o descargá tu borrador antes de aceptar cambios.');const id=current?.id;state=await api('/api/proposal/decide',{project:state.id,proposal:b.dataset.accept||b.dataset.reject,accept:!!b.dataset.accept});if(id && b.dataset.accept){sessionStorage.removeItem(draftKey());openDocument(id,true);}renderAssistant();notice(b.dataset.accept?'Bloque aceptado. La versión anterior se conserva.':'Propuesta rechazada.');});
$('decision-form').onsubmit=action(async e=>{e.preventDefault();state=await api('/api/decision',{project:state.id,text:$('decision-text').value,status:$('decision-status').value});$('decision-text').value='';renderAssistant();notice('Decisión registrada.');});
$('new-thread').onclick=action(async()=>{if(!confirm('¿Abrir una conversación nueva? Conservaremos las anteriores como historial y las decisiones registradas.'))return;state=await api('/api/thread/reset',{project:state.id});notice('El próximo mensaje abrirá una conversación nueva.');});
$('export').onclick=action(async()=>{if(!state)return;if(dirty)throw new Error('Guardá antes de exportar el proyecto o descargá el borrador como Markdown.');const blob=await api(`/api/projects/${state.id}/export`);download(blob,'story-workbench.zip');});
$('focus').onclick=()=>{const focused=document.body.classList.toggle('focus');$('focus').textContent=focused?'⛶ Salir de foco':'⛶ Modo foco';$('focus').setAttribute('aria-pressed',focused);if(current)$('editor').focus();};
$('inspire').onclick=()=>{if(backgroundURL){URL.revokeObjectURL(backgroundURL);backgroundURL=null;$('ambient-image').hidden=true;$('inspire').textContent='◐ Ambiente';}else $('background-file').click();};
$('background-file').onchange=action(e=>{const file=e.target.files[0];if(!file)return;if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>10000000)throw new Error('Usá una imagen PNG, JPEG o WebP de hasta 10 MB.');backgroundURL=URL.createObjectURL(file);$('ambient-image').src=backgroundURL;$('ambient-image').hidden=false;$('inspire').textContent='◑ Quitar ambiente';notice('Imagen local de esta pestaña. No se envía a Codex.');e.target.value='';});
window.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();$('save').click();}if((e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key.toLowerCase()==='f'){e.preventDefault();$('focus').click();}});
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
(async()=>{try{const projects=await refreshProjects();if(projects.length){const saved=sessionStorage.getItem('sw-project');await openProject(projects.some(p=>p.id===saved)?saved:projects[0].id);}else{$('welcome').hidden=false;$('export').disabled=true;}}catch(error){$('welcome').hidden=false;notice(error.message,true);}})();
setInterval(poll,1500);
