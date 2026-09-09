'use strict';
const { app, BrowserWindow, dialog, shell, session, protocol } = require('electron');
const { spawn } = require('node:child_process');
const { join } = require('node:path');
const { mkdirSync } = require('node:fs');
const readline = require('node:readline');
let child, window, origin, token, closing = false;
const uiOrigin = 'workbench://app';
protocol.registerSchemesAsPrivileged([{scheme:'workbench', privileges:{standard:true, secure:true, supportFetchAPI:true, corsEnabled:true}}]);
if (process.env.STORY_TEST_DATA) app.setPath('userData', process.env.STORY_TEST_DATA);
const lock = app.requestSingleInstanceLock();
if (!lock) app.quit();
else {
  app.on('second-instance', () => { if (window) { window.restore(); window.focus(); } });
  app.whenReady().then(start).catch(() => {
    dialog.showErrorBox('No se pudo abrir Story Workbench', 'Probá abrir la app nuevamente. Si continúa, reinstalá el paquete. Tus proyectos se conservan en los datos de la aplicación.');
    closing = true; child?.stdin.end(); app.quit();
  });
}
async function start() {
  const root = app.isPackaged ? join(process.resourcesPath, 'runtime') : join(app.getAppPath(), 'dist', 'runtime');
  const data = app.getPath('userData');
  mkdirSync(join(data, 'codex'), { recursive: true, mode: 0o700 });
  const windows = process.platform === 'win32';
  const command = windows ? join(root, 'python', 'python.exe') : join(root, 'server', 'story-server');
  const args = windows ? [join(root, 'server', 'app.py')] : [];
  const env = { ...process.env, STORY_DESKTOP: '1', STORY_VOICE_DIR: join(root, 'voice'), CODEX_HOME: join(data, 'codex'),
    STORY_CODEX_BINARY: join(root, 'codex', 'bin', windows ? 'codex.exe' : 'codex') };
  for (const key of Object.keys(env)) if (/^(OPENAI_|AZURE_OPENAI_|CODEX_API_|CODEX_THREAD_)/.test(key)) delete env[key];
  child = spawn(command, [...args, '--port', '0', '--data-dir', join(data, 'projects')], {
    env, windowsHide: true, stdio: ['pipe', 'pipe', 'ignore']
  });
  const ready = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('timeout')), 30000);
    child.once('error', reject); child.once('exit', () => reject(new Error('exit')));
    const lines = readline.createInterface({ input: child.stdout });
    lines.on('line', line => {
      try {
        const value = JSON.parse(line);
        if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(value.origin) || !/^[A-Za-z0-9_-]{43}$/.test(value.token)) return;
        clearTimeout(timeout); lines.close(); resolve(value);
      } catch { /* El backend puede emitir diagnósticos sin datos privados. */ }
    });
  });
  ({ origin, token } = ready);
  // A stable origin preserves theme, drafts and read/collapse state across launches.
  protocol.handle('workbench', async request => {
    const url = new URL(request.url);
    if (url.hostname !== 'app' || !['GET','POST'].includes(request.method)) return new Response('', {status:403});
    const headers = {Origin:origin};
    for (const name of ['Authorization','Content-Type']) if(request.headers.has(name)) headers[name]=request.headers.get(name);
    return fetch(origin + url.pathname + url.search, {method:request.method, headers,
      body:request.method==='POST'?await request.arrayBuffer():undefined, redirect:'error'});
  });
  const localFrame = contents => contents === window?.webContents && contents.getURL().startsWith(uiOrigin + '/');
  session.defaultSession.setPermissionRequestHandler((contents, permission, callback, details) => {
    callback(localFrame(contents) && permission === 'media' && details.isMainFrame &&
      details.mediaTypes?.length === 1 && details.mediaTypes[0] === 'audio');
  });
  session.defaultSession.setPermissionCheckHandler((contents, permission, requestingOrigin, details) =>
    localFrame(contents) && permission === 'media' && details.isMainFrame &&
    details.mediaType === 'audio' && requestingOrigin.replace(/\/$/,'') === uiOrigin);
  // Only the local UI may make requests; ChatGPT login opens in the system browser.
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
    callback({ cancel: !details.url.startsWith(origin + '/') && !details.url.startsWith(uiOrigin + '/') && !/^(blob:|data:|devtools:)/.test(details.url) });
  });
  window = new BrowserWindow({ width: 1440, height: 960, minWidth: 390, minHeight: 640,
    title: 'Story Workbench', autoHideMenuBar: true, show: false,
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true, spellcheck: true } });
  window.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsed = new URL(url);
      if (parsed.origin === 'https://auth.openai.com' && !parsed.username && !parsed.password)
        shell.openExternal(url).catch(() => dialog.showErrorBox('Navegador', 'No se pudo abrir el navegador predeterminado.'));
    } catch { /* No abrir URLs inesperadas. */ }
    return { action: 'deny' };
  });
  window.webContents.on('will-navigate', (event, url) => { if (!url.startsWith(uiOrigin + '/')) event.preventDefault(); });
  window.webContents.on('will-attach-webview', event => event.preventDefault());
  child.on('exit', () => { if (!closing) { dialog.showErrorBox('El servicio se detuvo', 'Cerrá y volvé a abrir la app. Los cambios guardados se conservan.'); app.quit(); } });
  await window.loadURL(`${uiOrigin}/#token=${token}`);
  window.show();
  if (process.env.STORY_DESKTOP_SMOKE === '1') {
    const safe = await window.webContents.executeJavaScript(`(async()=>{
      if(typeof require!=='undefined'||typeof process!=='undefined') return false;
      const headers={Authorization:'Bearer '+sessionStorage.getItem('sw-token'),'Content-Type':'application/json'};
      const response=await fetch('/api/projects',{method:'POST',headers,body:JSON.stringify({title:'Prueba empaquetada',demo:true})});
      if(!response.ok) return false;
      const project=await response.json();
      const exportResponse=await fetch('/api/projects/'+project.id+'/book.docx',{headers});
      if(!exportResponse.ok || !document.querySelector('#plan-dialog') || !document.querySelector('#ai-model'))return false;
      const before=localStorage.getItem('desktop-smoke');
      localStorage.setItem('desktop-smoke','persisted');
      return {persistent:before==='persisted',project:project.title==='Prueba empaquetada',origin:location.href.split('#')[0]};
    })()`);
    if (!safe || !safe.project) throw new Error('Renderer isolation/API');
    if(process.env.STORY_VOICE_SMOKE === '1') {
      const media=await window.webContents.executeJavaScript(`(async()=>{
        const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
        const audio=stream.getAudioTracks().length===1;stream.getTracks().forEach(track=>track.stop());
        let videoDenied=false;try{const camera=await navigator.mediaDevices.getUserMedia({video:true});camera.getTracks().forEach(track=>track.stop());}catch{videoDenied=true;}
        const headers={Authorization:'Bearer '+sessionStorage.getItem('sw-token'),'Content-Type':'application/json'};
        const response=await fetch('/api/voice/read',{method:'POST',headers,body:JSON.stringify({text:'Una biblioteca ficticia.'})});
        const audioBytes=response.ok?(await response.arrayBuffer()).byteLength:0;
        const dictation=await fetch('/api/voice/transcribe',{method:'POST',headers,body:JSON.stringify({pcm:btoa(String.fromCharCode(...new Uint8Array(16000)))})});
        return {audio,videoDenied,audioBytes,dictation:dictation.ok};
      })()`);
      if(!media.audio||!media.videoDenied||media.audioBytes<44||!media.dictation)throw new Error('Voice smoke failed');
      console.log('OK voz empaquetada: '+JSON.stringify(media));
    }
    console.log(JSON.stringify(safe));
    console.log('OK Electron: backend empaquetado, renderer aislado, interfaz cargada.');
    app.quit();
  }
}
app.on('window-all-closed', () => app.quit());
app.on('before-quit', event => {
  if (!child || closing) return;
  // Dejar que Electron consulte beforeunload antes de detener el backend.
  if (window && !window.isDestroyed()) {
    event.preventDefault();
    window.once('closed', () => { window = null; app.quit(); });
    window.close();
    return;
  }
  event.preventDefault(); closing = true;
  child.stdin.end();
  const timeout = setTimeout(() => { child.kill(); app.quit(); }, 24000);
  child.once('exit', () => { clearTimeout(timeout); app.quit(); });
});
