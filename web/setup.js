'use strict';
let setupStep=0;
function setupSeen(){try{return localStorage.getItem('sw-setup-seen')==='1';}catch{return false;}}
function rememberSetup(){try{localStorage.setItem('sw-setup-seen','1');}catch{notice('No se pudo recordar que completaste el inicio.',true);}}
function renderSetup(){
  document.querySelectorAll('[data-setup-step]').forEach(el=>el.hidden=Number(el.dataset.setupStep)!==setupStep);
  $('setup-progress').textContent=`Paso ${setupStep+1} de 4`;
  $('setup-back').disabled=setupStep===0;$('setup-next').hidden=setupStep===3;
  document.querySelector(`[data-setup-step="${setupStep}"] h3`).focus();
}
async function openSetup(){
  const projects=await refreshProjects();
  $('setup-project').replaceChildren(...projects.map(p=>new Option(p.title,p.id)));
  if(state)$('setup-project').value=state.id;
  $('setup-existing').hidden=projects.length===0;
  $('setup-appearance').append($('appearance-controls'));
  setupStep=0;showDialog($('setup-dialog'));renderSetup();
}
async function skipSetup(){
  rememberSetup();$('setup-dialog').close();
  if(!state&&$('setup-project').value)await openProject($('setup-project').value,false);
  else if(!state)$('welcome').hidden=false;
}
$('setup-open').onclick=action(async()=>{$('settings-dialog').close();await openSetup();});
$('setup-skip').onclick=action(skipSetup);
$('setup-dialog').addEventListener('close',()=>$('settings-general').insertBefore($('appearance-controls'),$('inspire')));
$('setup-dialog').oncancel=event=>{event.preventDefault();action(skipSetup)();};
$('setup-back').onclick=()=>{setupStep--;renderSetup();};
$('setup-next').onclick=()=>{setupStep++;renderSetup();};
$('setup-account').onclick=()=>$('account-open').click();
$('setup-voice').onclick=()=>$('realtime-settings').click();
$('setup-new').onclick=action(async()=>{rememberSetup();$('setup-dialog').close();await createProject();});
$('setup-folder').onclick=action(async()=>{rememberSetup();$('setup-dialog').close();await createProject(false,true);});
$('setup-workspace').onclick=()=>{$('setup-dialog').close();openSettings();$('workspace-path').focus();};
$('setup-resume').onclick=action(async()=>{const id=$('setup-project').value;if(!id)return;rememberSetup();$('setup-dialog').close();await openProject(id);});

// Destinos explícitos compartidos por teclado y voz; nunca aprobaciones ni clicks arbitrarios.
const navigationLabels={back:'Cerrar sección abierta',conversation:'Conversación',proposals:'Propuestas',decisions:'Decisiones',notices:'Avisos',library:'Biblioteca',material:'Material',settings:'Configuración',model:'Modelo y esfuerzo',voice:'Configuración de voz',account:'Cuenta ChatGPT',setup:'Asistente inicial',help:'Ayuda',images:'Imágenes experimentales',book:'Libro 3D',plan:'Plan y avance',translation:'Traducción'};
async function navigateWorkbench(target){
  if(!Object.hasOwn(navigationLabels,target))throw new Error('Sección no permitida.');
  const modal=topDialog();
  if(target==='back'){
    if(!modal)return;
    const closers={'image-viewer':'image-viewer-close','images-dialog':'images-close','settings-dialog':'settings-close','help-dialog':'help-close','account-dialog':'account-close','realtime-dialog':'realtime-close','engine-dialog':'engine-close','navigation-dialog':'navigation-close','setup-dialog':'setup-skip'};
    if(modal.id==='book-dialog'&&!bookDirty){$('book-close').click();return;}
    if(!closers[modal.id])throw new Error('Esta sección puede tener cambios pendientes. Usá su botón de cierre para revisarlos.');
    $(closers[modal.id]).click();return;
  }
  if(modal)throw new Error('Cerrá el diálogo actual antes de cambiar de sección.');
  if(target==='model'&&state){
    if(document.body.classList.contains('focus'))$('focus').click();showPanel('conversation');
    const control=selectedEngine()==='codex'?$('ai-model'):$('chat-engine');
    if(control.disabled){$('account-open').click();}else control.focus();
  }else if(['settings','model','voice'].includes(target)){
    openSettings();if(target==='model')$('engine-open').focus();if(target==='voice')$('realtime-settings').focus();
  }else if(target==='setup')await openSetup();
  else if(target==='account')$('account-open').click();
  else if(target==='help')openHelp();
  else{
    if(!state)throw new Error('Abrí un proyecto primero.');
    if(document.body.classList.contains('focus'))$('focus').click();
    if(['conversation','proposals','decisions','notices'].includes(target)){
      showPanel(target);const panel=$(target+'-panel');panel.tabIndex=-1;panel.focus();if(target==='conversation')$('prompt').focus();
    }else if(target==='library'){
      document.body.classList.add('library-open');$('library-toggle').setAttribute('aria-expanded','true');$('search').focus();
    }else if(target==='material'){showMaterial();$('editor').focus();}
    else{const button=$(target+'-open');if(button.hidden||button.disabled)throw new Error('Sección no disponible en este modo.');button.click();}
  }
}
function renderNavigation(){
  const query=$('navigation-search').value.trim().toLocaleLowerCase('es');
  $('navigation-options').replaceChildren();
  for(const [target,label] of Object.entries(navigationLabels)){
    if(!label.toLocaleLowerCase('es').includes(query))continue;
    const button=document.createElement('button');button.textContent=label;button.className='secondary';
    button.onclick=action(async()=>{$('navigation-dialog').close();await navigateWorkbench(target);});$('navigation-options').append(button);
  }
  $('navigation-empty').hidden=!!$('navigation-options').childElementCount;
}
$('navigation-open').onclick=()=>{if(document.querySelector('dialog[open]'))return;$('navigation-search').value='';renderNavigation();showDialog($('navigation-dialog'));$('navigation-search').focus();};
$('navigation-close').onclick=()=>$('navigation-dialog').close();
$('navigation-search').oninput=renderNavigation;
$('navigation-search').onkeydown=event=>{if(['ArrowDown','Enter'].includes(event.key)){event.preventDefault();const first=$('navigation-options').firstElementChild;if(event.key==='Enter')first?.click();else first?.focus();}};
window.addEventListener('keydown',event=>{
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();$('navigation-open').click();}
  if((event.ctrlKey||event.metaKey)&&event.key===','){event.preventDefault();if(!document.querySelector('dialog[open]'))openSettings();}
  const tab=event.target.closest?.('[role=tab]');
  if(tab&&['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){
    const tabs=[...tab.parentElement.querySelectorAll('[role=tab]')],index=tabs.indexOf(tab);
    const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
    event.preventDefault();tabs[next].click();tabs[next].focus();
  }
});
