"""Ayuda y recuperación de UI con ficción temporal, sin llamadas IA ni micrófono."""
from pathlib import Path
import sys
import tempfile
import threading
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.app import AppServer
from test_desktop_features import MODELS
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-ux-') as directory:
    server = AppServer(0, directory)
    server.account.set(status='signed_out')
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1440, 'height':1000})
            errors = []; writes = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda r: writes.append(r.url) if r.method=='POST' else None)
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token)
            page.locator('#welcome').wait_for()
            assert not page.locator('#help-dialog').is_visible()
            page.locator('#help-open').click()
            page.locator('#help-search').fill('microfono')
            assert page.locator('#help-voice').is_visible()
            assert page.locator('#help-voice').evaluate('(el)=>el.open')
            page.locator('#help-search').fill('<script>no-existe</script>')
            assert page.locator('#help-empty').is_visible()
            page.locator('#help-clear').click()
            assert page.locator('.help-topic:visible').count()==14
            page.screenshot(path='/tmp/story-workbench-help.png', full_page=True)
            page.keyboard.press('Escape')
            assert writes==[] and server.store.list_projects()==[]
            page.get_by_role('button', name='Explorar un proyecto ficticio').click()
            page.locator('#editor').wait_for()
            project = server.store.list_projects()[0]['id']
            prompt = page.locator('#prompt')
            page.locator('#mode').select_option('diagnosis')
            prompt.fill('Una idea todavía sin enviar.')
            editor = page.locator('#editor'); original = editor.input_value()
            editor.fill(original+'\nNota sin guardar.'); prompt.focus()
            before = len(writes)
            page.keyboard.press('F1'); page.keyboard.press('Escape')
            assert prompt.evaluate('(el)=>el===document.activeElement')
            assert prompt.input_value()=='Una idea todavía sin enviar.'
            assert page.locator('#mode').input_value()=='diagnosis'
            assert editor.input_value().endswith('Nota sin guardar.') and len(writes)==before
            page.route('**/help.js', lambda route: (time.sleep(.5), route.continue_()))
            page.reload(); page.locator('#workspace').wait_for()
            page.unroute('**/help.js')
            assert prompt.input_value()=='Una idea todavía sin enviar.'
            assert page.locator('#mode').input_value()=='diagnosis'
            assert editor.input_value().endswith('Nota sin guardar.')
            page.locator('#save').click()
            page.wait_for_function("() => document.querySelector('#save-state').textContent==='Guardado local'")
            # Ayuda anidada conserva las fichas pendientes del diálogo que estaba abierto.
            page.locator('#plan-open').click()
            synopsis = page.locator('.plan-card textarea').first
            synopsis.fill('Un faro ficticio que cambia de lugar.')
            page.locator('#plan-dialog [data-help=plan]').click()
            assert page.locator('#help-plan').evaluate('(el)=>el.open')
            page.keyboard.press('Escape')
            assert page.locator('#plan-dialog').is_visible()
            assert synopsis.input_value()=='Un faro ficticio que cambia de lugar.'
            page.locator('.plan-card button[type=submit]').first.click()
            page.get_by_text('Ficha guardada.', exact=True).wait_for()
            page.locator('#plan-close').click()
            page.locator('#mode').select_option('diagnosis')
            assert 'sin reescribir' in page.locator('#mode-hint').inner_text()
            page.locator('#settings-open').click();page.locator('.task-guidance [data-help]').click()
            assert page.locator('#help-review').evaluate('(el)=>el.open')
            page.keyboard.press('Escape')
            page.locator('#settings-close').click();assert page.locator('#export').get_attribute('title')
            assert page.locator('#tip-export').inner_text()
            page.locator('#search').fill('palabra-inexistente')
            assert 'No hay coincidencias' in page.locator('#documents').inner_text()
            page.locator('#search-clear').click()
            assert page.locator('.document-item').count()==4
            # Escape no reutiliza el resultado de una creación anterior.
            page.locator('#new-doc').click(); page.locator('#new-name').fill('Nota ficticia')
            page.locator('#name-dialog button[value=ok]').click()
            page.wait_for_function("() => document.querySelectorAll('.document-item').length===5")
            page.locator('#new-doc').click(); page.locator('#new-name').fill('No crear')
            page.keyboard.press('Escape'); page.wait_for_timeout(100)
            assert len(server.store.snapshot(project)['documents'])==5
            # Avisos persistentes en su pestaña, sin superponer mensajes al chat.
            page.locator('[data-panel=notices]').click();page.locator('#notices-clear').click()
            page.locator('[data-panel=conversation]').click()
            page.evaluate("notice('Error ficticio persistente',true);notice('Éxito posterior')")
            assert not page.locator('#notice').is_visible()
            assert page.locator('#notices-count').inner_text()=='2'
            assert page.locator('#conversation-panel').is_visible()
            page.locator('[data-panel=notices]').click()
            assert not page.locator('#notices-count').is_visible()
            assert page.locator('#notices-list .notice-error').inner_text().find('Error ficticio persistente')>=0
            assert page.locator('#notices-list').inner_text().find('Éxito posterior')>=0
            page.evaluate("notice('<script>window.injected=true</script>',true)")
            assert not page.locator('#notices-list script').count() and not page.evaluate('window.injected')
            assert not page.locator('#notices-count').is_visible()
            page.locator('[data-panel=conversation]').click()
            page.evaluate("notice('Repetido');notice('Repetido')")
            assert page.locator('#notices-count').inner_text()=='1'
            page.evaluate("navigateWorkbench('notices')")
            assert '×2' in page.locator('#notices-list').inner_text()
            page.locator('#notices-clear').click();assert page.locator('#notices-list .notice-entry').count()==0
            before=len(writes)
            page.evaluate("for(let i=0;i<105;i++)notice('Aviso de límite '+i)")
            assert page.locator('#notices-list .notice-entry').count()==100 and len(writes)==before
            assert page.locator('#notices-list .notice-entry').last.locator('p').inner_text()=='Aviso de límite 5'
            page.locator('#notices-clear').click()
            page.locator('[data-panel=conversation]').click()
            # Hilo ficticio ya iniciado: cambiar a guiado no inicia una entrevista real.
            run = dict(id='ux-run', mode='interview', prompt='Una historia ficticia', status='completed',
                       text='¿Qué querés explorar?\n'*160, sources=[], date=0)
            with server.store.lock:
                data=server.store.load(project); data['runs']=[run]; server.store.persist(data)
            page.locator('.run').wait_for()
            page.locator('#settings-open').click();page.locator('#workflow').select_option('guided');page.locator('#settings-close').click()
            page.wait_for_function("() => document.body.classList.contains('guided')")
            # Acciones junto al texto; los selectores comparten una fila inferior.
            rects=page.evaluate("() => ['prompt','send','dictate','auto-read','mode','ai-model','ai-effort'].map(id=>{const r=$(id).getBoundingClientRect();return {top:r.top,bottom:r.bottom,width:r.width};})")
            assert all(r['top']<rects[0]['bottom'] and r['bottom']>rects[0]['top'] for r in rects[1:3]),rects
            assert rects[3]['top']>=rects[1]['bottom'],rects
            assert abs(rects[2]['top']-rects[1]['top'])<1 and rects[2]['bottom']>=rects[3]['bottom'],rects
            assert page.locator('#send').evaluate('el=>Math.abs(el.getBoundingClientRect().width-el.parentElement.getBoundingClientRect().width)<1')
            assert page.locator('#dictate').evaluate('el=>parseFloat(getComputedStyle(el).borderTopLeftRadius)<el.clientWidth/2')
            # El compositor compacto conserva un blanco clickeable y nombre accesible.
            assert rects[1]['bottom']-rects[1]['top']>=36 and rects[1]['width']>=36,rects
            assert page.get_by_role('button',name='Enviar',exact=True).get_attribute('id')=='send'
            assert page.locator('#send [aria-hidden=true]').inner_text()=='↵'
            assert max(r['bottom'] for r in rects[4:])-min(r['bottom'] for r in rects[4:])<3,rects
            page.screenshot(path='/tmp/sw-composer-wide.png',full_page=True)
            with server.store.lock:
                data=server.store.load(project);data['runs'][0]['status']='running';server.store.persist(data)
            page.locator('.run-text.is-streaming').wait_for()
            assert page.locator('#cancel').is_visible()
            assert 'presioná Escape' in page.locator('[data-working-since]').inner_text()
            first_elapsed=page.locator('[data-working-since]').inner_text()
            page.wait_for_function('(previous)=>document.querySelector("[data-working-since]").textContent!==previous',arg=first_elapsed)
            with server.store.lock:
                data=server.store.load(project);data['runs'][0].update(waiting=True,last_activity=time.time()-61);server.store.persist(data)
            page.wait_for_function('()=>document.querySelector("[data-working-since]").textContent.startsWith("Sin actividad")')
            assert 'podés esperar' in page.locator('[data-working-since]').inner_text()
            with server.store.lock:
                data=server.store.load(project);data['runs'][0]['waiting']=False;server.store.persist(data)
            page.wait_for_function('()=>document.querySelector("[data-working-since]").textContent.startsWith("Trabajando")')
            interrupts=[]
            page.route('**/api/run/cancel',lambda route:(interrupts.append(route.request.post_data_json),route.fulfill(status=200,content_type='application/json',body='{}')))
            page.locator('#settings-open').click();page.keyboard.press('Escape')
            assert interrupts==[]
            page.locator('#prompt').focus();page.keyboard.press('Escape')
            page.wait_for_function("() => !$('cancel').hasAttribute('aria-busy')")
            assert len(interrupts)==1 and interrupts[0]['run']=='ux-run'
            page.unroute('**/api/run/cancel')

            assert page.locator('.run-output > summary .work-spinner').is_visible()
            assert page.locator('.work-spinner').evaluate('el=>getComputedStyle(el).animationName')=='workbench-wait'
            assert page.locator('#cancel').evaluate('el=>getComputedStyle(el).backgroundColor')=='rgb(180, 35, 50)'
            assert page.locator('.is-streaming').evaluate('el=>getComputedStyle(el,"::after").animationName')=='writing-cursor'
            page.emulate_media(reduced_motion='reduce')
            assert page.locator('.work-spinner').evaluate('el=>getComputedStyle(el).animationName')=='none'
            assert page.locator('.is-streaming').evaluate('el=>getComputedStyle(el,"::after").animationName')=='none'
            page.emulate_media(reduced_motion='no-preference')
            with server.store.lock:
                data=server.store.load(project);data['runs'][0]['text']+='Nuevo fragmento';server.store.persist(data)
            page.wait_for_function("() => document.querySelector('.is-streaming').textContent.trimEnd().endsWith('Nuevo fragmento')")
            with server.store.lock:
                data=server.store.load(project);data['runs'][0]['status']='completed';server.store.persist(data)
            page.wait_for_function("() => !document.querySelector('.is-streaming')")
            assert page.locator('#cancel').is_hidden()
            assert page.locator('.work-spinner').count()==0

            page.locator('#runs').evaluate('(el)=>el.scrollTop=120')
            page.locator('#latest-answer').wait_for()
            with server.store.lock:
                data=server.store.load(project); data['runs'][0]['text']+='Final ficticio'; server.store.persist(data)
            page.wait_for_function("() => document.querySelector('.run-text').textContent.trimEnd().endsWith('Final ficticio')")
            assert page.locator('#runs').evaluate('(el)=>el.scrollHeight-el.scrollTop-el.clientHeight')<2
            assert not page.locator('#latest-answer').is_visible()
            page.locator('#runs').evaluate('(el)=>el.scrollTop=120')
            with server.store.lock:
                data=server.store.load(project);data['runs'].append(dict(run,id='ux-new-message',prompt='Mensaje nuevo del autor',text=''));server.store.persist(data)
            page.get_by_text('Mensaje nuevo del autor',exact=True).wait_for()
            assert page.locator('#runs').evaluate('(el)=>el.scrollHeight-el.scrollTop-el.clientHeight')<2
            # Respuesta HTTP demorada: no borrar lo escrito después de pulsar Enviar.
            server.account.set(status='connected', models=MODELS)
            page.locator('#account-open').click(); page.locator('#account-close').click()
            page.locator('.composer-bottom #ai-model:not([disabled])').wait_for()
            sent = []
            def intercept(route):
                sent.append(route.request.post_data_json)
                prompt.fill('Una segunda idea mientras se envía.')
                route.fulfill(status=200, content_type='application/json', body='{}')
            page.route('**/api/run', intercept)
            prompt.fill('Primera línea'); prompt.press('Shift+Enter'); prompt.press('End')
            assert prompt.input_value()=='Primera línea\n' and sent==[]
            # Confirmar composición (IME) o mantener Enter no debe enviar.
            for attributes in [{'isComposing':True},{'keyCode':229},{'repeat':True}]:
                prompt.dispatch_event('keydown',dict(key='Enter',**attributes))
            page.wait_for_timeout(100); assert sent==[]
            page.evaluate("$('send').disabled=true")
            prompt.press('Enter'); assert prompt.input_value()=='Primera línea\n' and sent==[]
            page.evaluate("$('send').disabled=false")
            unseen=page.locator('.new-tag').count();assert unseen>0
            prompt.fill('   '); prompt.press('Enter')
            page.wait_for_function("() => !$('send').hasAttribute('aria-busy')")
            assert sent==[]
            assert page.locator('.new-tag').count()==unseen
            prompt.fill('Primera idea'); prompt.press('Enter')
            page.wait_for_function("() => document.querySelector('#prompt').value.startsWith('Una segunda')")
            assert sent[0]['prompt']=='Primera idea'
            page.wait_for_function("() => !document.querySelector('.new-tag')")
            page.wait_for_function("() => !$('send').hasAttribute('aria-busy')")
            prompt.fill('Otra línea'); prompt.press('Shift+Enter'); prompt.type('Continuación')
            assert len(sent)==1
            prompt.press('Control+Enter')
            page.wait_for_function("() => document.querySelector('#prompt').value.startsWith('Una segunda')")
            assert len(sent)==2 and sent[1]['prompt']=='Otra línea\nContinuación'
            page.reload(); page.locator('#workspace').wait_for()
            assert prompt.input_value()=='Una segunda idea mientras se envía.'
            assert page.locator('.new-tag').count()==0
            with server.store.lock:
                data=server.store.load(project);data['runs'].append(dict(run,id='fresh-reply',text='Nueva respuesta ficticia'));server.store.persist(data)
            page.locator('[data-output=fresh-reply] .new-tag').wait_for()
            assert page.locator('.new-tag').count()==1
            second = server.store.create('Otro universo ficticio', workflow='guided')['id']
            with server.store.lock:
                data=server.store.load(second); data['runs']=[run]; server.store.persist(data)
            page.reload(); page.locator('#project').select_option(second)
            page.wait_for_function("() => document.querySelector('#project-title').textContent==='Otro universo ficticio'")
            assert prompt.input_value()==''
            assert 'Todavía no hay documentos' in page.locator('#documents').inner_text()
            page.locator('#project').select_option(project)
            page.wait_for_function('(id) => state?.id===id', arg=project)
            assert prompt.input_value()=='Una segunda idea mientras se envía.'
            page.screenshot(path='/tmp/story-workbench-ux.png', full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.locator('#library-toggle').wait_for()
            assert not page.locator('.sources').is_visible()
            page.locator('#library-toggle').click()
            assert page.locator('.sources').is_visible()
            assert page.locator('#library-toggle').get_attribute('aria-expanded')=='true'
            page.locator('#library-toggle').click()
            page.screenshot(path='/tmp/story-workbench-ux-compact.png', full_page=True)
            page.emulate_media(color_scheme='dark')
            page.locator('#settings-open').click();page.locator('[data-help=voice]').click()
            assert page.locator('#help-voice').evaluate('(el)=>el.open')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('#help-dialog').evaluate('(el)=>el.scrollWidth<=el.clientWidth')
            page.screenshot(path='/tmp/story-workbench-help-compact.png', full_page=True)
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown(); server.server_close()
print('OK UX: ayuda sin efectos, búsqueda, teclado/foco, formularios, borradores, errores persistentes, scroll y vista compacta. Sin llamadas IA.')
