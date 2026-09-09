(async()=>{
  const headers={Authorization:'Bearer __TOKEN__','Content-Type':'application/json'};
  const finish=ok=>fetch('/__smoke',{method:'POST',headers,body:ok?'ok':'failed'});
  try{
    for(let n=0;n<100&&typeof openSetup!=='function';n++)await new Promise(r=>setTimeout(r,100));
    if(typeof require!=='undefined'||!document.querySelector('#setup-dialog'))throw Error('isolation');
    if(localStorage.getItem('tauri-smoke')){if(document.documentElement.dataset.theme!=='dark')throw Error('persisted-theme');}
    else for(let n=0;n<100&&!document.querySelector('#setup-dialog').open;n++)await new Promise(r=>setTimeout(r,100));
    await skipSetup();
    const response=await fetch('/api/projects',{method:'POST',headers,body:JSON.stringify({title:'Ficción Tauri',demo:true})});
    if(!response.ok)throw Error('create');const project=await response.json();await openProject(project.id);
    if(!document.querySelector('#editor').value.includes('llave azul'))throw Error('editor');
    await navigateWorkbench('settings');document.querySelector('#theme').value='dark';document.querySelector('#theme').onchange();
    await navigateWorkbench('back');await navigateWorkbench('book');
    if(document.querySelector('#book-width').value!=='152.4')throw Error('book');
    document.querySelector('#book-close').click();
    const book=await fetch('/api/projects/'+project.id+'/book.docx',{headers});if(!book.ok)throw Error('export');
    const voice=await fetch('/api/voice-storage',{headers});if((await voice.json()).available)throw Error('vault-stage');
    localStorage.setItem('tauri-smoke','1');await finish(true);
  }catch(error){await finish(false);}
})();
