(async()=>{
  if(location.protocol==='about:')return;
  const headers={Authorization:'Bearer __TOKEN__','Content-Type':'application/json'};
  let stage='startup';
  const finish=ok=>fetch('/__smoke',{method:'POST',headers,body:ok?'ok':stage});
  try{
    for(let n=0;n<100&&typeof openSetup!=='function';n++)await new Promise(r=>setTimeout(r,100));
    if(typeof require!=='undefined'||!document.querySelector('#setup-dialog'))throw Error('isolation');
    if(localStorage.getItem('tauri-smoke')){if(document.documentElement.dataset.theme!=='dark'||document.querySelector('#voice-volume').value!=='35')throw Error('persisted-preferences');}
    else for(let n=0;n<100&&!document.querySelector('#setup-dialog').open;n++)await new Promise(r=>setTimeout(r,100));
    if(document.querySelector('#setup-dialog').open){
      if(document.querySelector('#setup-progress').textContent!=='Paso 1 de 4'||!document.querySelector('#setup-appearance #theme'))throw Error('setup-theme');
      openVoiceSettings();notice('Error ficticio de configuración',true);
      const alert=document.querySelector('#notice'),box=alert.getBoundingClientRect();
      if(alert.parentElement.id!=='realtime-dialog'||!alert.contains(document.elementFromPoint(box.x+20,box.y+20)))throw Error('modal-alert');
      document.querySelector('#notice-close').click();document.querySelector('#realtime-close').click();
    }
    await skipSetup();
    const response=await fetch('/api/projects',{method:'POST',headers,body:JSON.stringify({title:'Ficción Tauri',demo:true})});
    if(!response.ok)throw Error('create');const project=await response.json();await openProject(project.id);
    if(!document.querySelector('#editor').value.includes('llave azul'))throw Error('editor');
    if(!document.querySelector('.microphone-controls #auto-read')||document.querySelector('.local-badge')||document.querySelectorAll('#appearance-controls select').length!==1)throw Error('composer-theme');
    await navigateWorkbench('settings');document.querySelector('#theme').value='dark';document.querySelector('#theme').onchange();
    $('voice-volume').value='35';$('voice-volume').oninput();
    await navigateWorkbench('back');await navigateWorkbench('book');
    if(document.querySelector('#book-width').value!=='152.4')throw Error('book');
    document.querySelector('#book-close').click();
    const book=await fetch('/api/projects/'+project.id+'/book.docx',{headers});if(!book.ok)throw Error('export');
    stage='export-dialog';
    if(__EXPORT_TEST__){
      if(!window.storyDesktop)throw Error('desktop-marker');
      const denied=await fetch('/api/desktop/save?name=libro.docx',{method:'POST',body:'unauthorized'});
      if(denied.status!==401)throw Error('export-auth');
      const invalid=await fetch('/api/desktop/save?name=..%2Fsecret.md',{method:'POST',headers,body:'invalid'});
      if(invalid.status!==400)throw Error('export-path');
      if(!await download(await book.blob(),'libro.docx'))throw Error('save-dialog');
      if(await download(new Blob(['No guardar']),'cancelado.md'))throw Error('cancel-dialog');
      if(!await download(new Blob([]),'vacio.md'))throw Error('empty-dialog');
      stage='folder-dialog';
      const deniedFolder=await fetch('/api/desktop/folder',{method:'POST',body:'{}'});
      if(deniedFolder.status!==401)throw Error('folder-auth');
      const folder=await api('/api/desktop/folder',{});
      if(!folder.path)throw Error('folder-select');
      const preview=await api('/api/import/preview',{path:folder.path});
      if(preview.files.length!==1||preview.files[0].name!=='cuento.md')throw Error('folder-preview');
      const imported=await api('/api/projects',{title:'Carpeta ficticia',workflow:'guided',import_folder:{path:folder.path,files:['cuento.md']}});
      const snapshot=await api('/api/projects/'+imported.id);
      if(snapshot.documents.length!==1||snapshot.documents[0].selected)throw Error('folder-copy');
      if((await api('/api/desktop/folder',{})).path!==null)throw Error('folder-cancel');
    }
    stage='vault';
    const call=async(path,body)=>{const r=await fetch(path,{headers,method:body?'POST':'GET',...(body?{body:JSON.stringify(body)}:{})});if(!r.ok)throw Error('http');return r.json();};
    const second=!!localStorage.getItem('tauri-smoke');
    for(const [storage,keyPath,statusPath] of [['/api/voice-storage','/api/realtime/key','/api/realtime'],['/api/engine-storage','/api/engine/key','/api/engines']]){
      const vault=await call(storage);if(!vault.available||!!vault.stored.gemini!==second)throw Error('vault-state');
      if(second){
        const status=await call(statusPath);
        const configured=statusPath==='/api/realtime'?status.providers.gemini:status.gemini;
        if(!configured)throw Error('restore');
        await call(keyPath,{provider:'gemini',key:''});
        if((await call(storage)).stored.gemini)throw Error('forget');
      }else{
        await call(keyPath,{provider:'gemini',key:'AQ.fixture-not-a-real-key-tauri',remember:true});
        if(!(await call(storage)).stored.gemini)throw Error('save');
        const denied=await fetch(storage,{headers:{Authorization:'Bearer invalid'}});if(denied.status!==401)throw Error('authorization');
        const bad=await fetch(keyPath,{method:'POST',headers,body:JSON.stringify({provider:'gemini',key:'bad',remember:true})});if(bad.ok||!(await call(storage)).stored.gemini)throw Error('invalid-key');
      }
    }
    stage='audio-capabilities';
    stage='secure-context';if(!isSecureContext)throw Error('secure');
    stage='media-devices';if(!navigator.mediaDevices?.getUserMedia)throw Error('media');
    const hasRTC=typeof RTCPeerConnection==='function';
    stage='audio-worklet';
    const context=new AudioContext({sampleRate:16000});
    await context.audioWorklet.addModule('/voice-capture.js');
    const node=new AudioWorkletNode(context,'voice-capture');node.disconnect();await context.close();
    stage='microphone';
    await startDictation();
    if(!recording?.node)throw Error('capture');
    const tracks=recording.stream.getTracks();
    if(hasRTC){const peer=new RTCPeerConnection({iceServers:[]});peer.addTrack(tracks[0],recording.stream);
    try{if(!(await peer.createOffer()).sdp.includes('m=audio'))throw Error('offer');}finally{peer.close();}}
    await new Promise(r=>setTimeout(r,600));
    if(recording.samples===0)throw Error('samples');
    await finishDictation();
    if(recording||transcribing||tracks.some(t=>t.readyState!=='ended'))throw Error('release');
    let denied=false;try{const camera=await navigator.mediaDevices.getUserMedia({video:true});camera.getTracks().forEach(t=>t.stop());}catch{denied=true;}
    if(!denied)throw Error('camera');
    stage='gemini-transport';
    const originalFetch=window.fetch,originalSocket=window.WebSocket,sent=[];
    window.fetch=(input,options)=>['/api/realtime/connect','/api/realtime/read-session'].includes(String(input))?Promise.resolve(new Response(JSON.stringify({token:'fixture',setup:{},model:'gpt-realtime'}),{headers:{'Content-Type':'application/json'}})):originalFetch(input,options);
    window.WebSocket=class {
      static OPEN=1;readyState=1;
      constructor(url){this.openai=url.includes('api.openai.com');setTimeout(()=>{this.onopen?.();this.onmessage?.({data:JSON.stringify(this.openai?{type:'session.created'}:{setupComplete:{}})});},20);}
      send(value){const data=JSON.parse(value);sent.push(data);
        if(data.type==='response.create'||data.realtimeInput?.text)setTimeout(()=>{
          const samples=new Int16Array(2400);samples.fill(1000);const pcm=btoa(String.fromCharCode(...new Uint8Array(samples.buffer)));
          for(const message of this.openai?[{type:'response.output_audio.delta',delta:pcm},{type:'response.done',response:{status:'completed'}}]:[{serverContent:{modelTurn:{parts:[{inlineData:{mimeType:'audio/pcm;rate=24000',data:pcm}}]}}},{serverContent:{turnComplete:true}}])this.onmessage?.({data:JSON.stringify(message)});
        },10);
      }
      close(){this.readyState=3;}
    };
    try{
      $('realtime-provider').value='gemini';realtimeConfigured=true;realtimeConsent=true;$('realtime-enabled').checked=true;
      await startRealtime();await new Promise(r=>setTimeout(r,800));
      if(!realtime?.ready||!sent.some(message=>message.realtimeInput?.audio))throw Error('gemini-pcm');
      playGeminiAudio(realtime,{mimeType:'audio/pcm;rate=24000',data:btoa(String.fromCharCode(...new Uint8Array(2400)))});
      if(Math.abs(realtime.volumeNode.gain.value-.35)>.00001)throw Error('voice-volume');
      await new Promise(r=>setTimeout(r,150));
      const geminiTracks=realtime.stream.getTracks();stopRealtime();
      if(geminiTracks.some(t=>t.readyState!=='ended'))throw Error('gemini-release');
      if(!hasRTC){
        $('realtime-provider').value='openai';let rejected=false;
        try{await startRealtime();}catch(error){rejected=error.message.includes('no está disponible');}
        if(!rejected||realtime)throw Error('webrtc-message');
      }
      stage='online-reading';
      const originalMicrophone=navigator.mediaDevices.getUserMedia;
      navigator.mediaDevices.getUserMedia=()=>{throw Error('La lectura no debe capturar audio.');};
      try{for(const provider of ['openai','gemini']){
        $('realtime-provider').value=provider;realtimeConfigured=true;realtimeConsent=true;$('realtime-enabled').checked=true;
        await readText('Narración ficticia sin micrófono.');
        if(readingActive||onlineReading||$('voice-status').textContent.includes('respaldo'))throw Error('online-reading');
      }}finally{navigator.mediaDevices.getUserMedia=originalMicrophone;}
    }finally{stopRealtime();window.fetch=originalFetch;window.WebSocket=originalSocket;$('realtime-enabled').checked=false;realtimeConsent=false;realtimeConfigured=false;}
    stage='reading';
    await readText('Una biblioteca ficticia.');
    if(readingActive)throw Error('reading');
    localStorage.setItem('tauri-smoke','1');
    await fetch('/__capabilities',{method:'POST',headers,body:JSON.stringify({webrtc:hasRTC})});await finish(true);
  }catch(error){await finish(false);}
})();
