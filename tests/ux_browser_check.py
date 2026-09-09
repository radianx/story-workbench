"""Ayuda y recuperación de UI con ficción temporal, sin llamadas IA ni micrófono."""
from pathlib import Path
import sys
import tempfile
import threading
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import AppServer
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
            page.locator('.task-guidance [data-help]').click()
            assert page.locator('#help-review').evaluate('(el)=>el.open')
            page.keyboard.press('Escape')
            assert page.locator('#export').get_attribute('title')
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
            # Los errores siguen legibles hasta cerrar; un éxito posterior no los pisa.
            page.evaluate("notice('Error ficticio persistente',true);notice('Éxito posterior')")
            page.wait_for_timeout(12500)
            assert page.locator('#notice').is_visible()
            assert page.locator('#notice-text').inner_text()=='Error ficticio persistente'
            page.locator('#notice-close').click(); assert not page.locator('#notice').is_visible()
            # Hilo ficticio ya iniciado: cambiar a guiado no inicia una entrevista real.
            run = dict(id='ux-run', mode='interview', prompt='Una historia ficticia', status='completed',
                       text='¿Qué querés explorar?\n'*160, sources=[], date=0)
            with server.store.lock:
                data=server.store.load(project); data['runs']=[run]; server.store.persist(data)
            page.locator('.run').wait_for()
            page.locator('#workflow').select_option('guided')
            page.wait_for_function("() => document.body.classList.contains('guided')")
            page.locator('#runs').evaluate('(el)=>el.scrollTop=120')
            page.locator('#latest-answer').wait_for()
            with server.store.lock:
                data=server.store.load(project); data['runs'][0]['text']+='Final ficticio'; server.store.persist(data)
            page.wait_for_function("() => document.querySelector('.run-text').textContent.endsWith('Final ficticio')")
            assert abs(page.locator('#runs').evaluate('(el)=>el.scrollTop')-120)<2
            page.locator('#latest-answer').click()
            assert not page.locator('#latest-answer').is_visible()
            # Respuesta HTTP demorada: no borrar lo escrito después de pulsar Enviar.
            server.account.set(status='connected', models=MODELS)
            page.locator('#account-open').click(); page.locator('#account-close').click()
            page.locator('#ai-summary').click(); page.locator('#ai-model:not([disabled])').wait_for()
            sent = []
            def intercept(route):
                sent.append(route.request.post_data_json)
                prompt.fill('Una segunda idea mientras se envía.')
                route.fulfill(status=200, content_type='application/json', body='{}')
            page.route('**/api/run', intercept)
            prompt.fill('Primera idea'); page.locator('#send').click()
            page.wait_for_function("() => document.querySelector('#prompt').value.startsWith('Una segunda')")
            assert sent[0]['prompt']=='Primera idea'
            page.reload(); page.locator('#workspace').wait_for()
            assert prompt.input_value()=='Una segunda idea mientras se envía.'
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
            page.locator('[data-help=voice]').click()
            assert page.locator('#help-voice').evaluate('(el)=>el.open')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('#help-dialog').evaluate('(el)=>el.scrollWidth<=el.clientWidth')
            page.screenshot(path='/tmp/story-workbench-help-compact.png', full_page=True)
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown(); server.server_close()
print('OK UX: ayuda sin efectos, búsqueda, teclado/foco, formularios, borradores, errores persistentes, scroll y vista compacta. Sin llamadas IA.')
