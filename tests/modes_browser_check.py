"""Modos y revisión humana con respuestas ficticias; sin llamadas IA."""
import sys
from pathlib import Path
import tempfile
import threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.app import AppServer
from src.workbench_modes import validate_translation
from test_modes import QUESTION,DRAFT
from test_desktop_features import MODELS
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-modes-browser-') as directory:
    server=AppServer(0,directory);server.account.set(status='connected',models=MODELS)
    async def execute(project,requested,docs):
        with server.store.lock:
            data=server.store.load(project);run=next(r for r in data['runs'] if r['id']==requested['id'])
            if run['mode']=='translate':
                value=DRAFT if any(r.get('translation_answer') for r in data['runs']) else QUESTION
                run['translation_result']=validate_translation(value,run['translation_context']);run['text']=value['message']
            else:run['text']='¿Qué experiencia querés crear para tu mesa?' if data['purpose']=='rpg' else '¿Qué intención querés conservar?'
            run['status']='completed';server.store.persist(data);server.assistant.active=None
    server.assistant.execute=execute
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#blank').click()
            page.locator('#project-name').fill('Traducción ficticia');page.locator('#wizard-next').click()
            page.locator('#wizard-purpose').select_option('translation')
            assert page.locator('[name=start-workflow][value=writing]').is_disabled()
            assert page.locator('#wizard-story').is_hidden()
            page.locator('#wizard-file').set_input_files(dict(name='Original.md',mimeType='text/markdown',buffer=b'Te quiero'))
            page.wait_for_function('()=>wizardDocuments.length===1')
            assert page.locator('#wizard-file').evaluate('el=>el.files[0].name')=='Original.md'
            page.get_by_text('No hay indicios suficientes o el texto mezcla idiomas.',exact=False).wait_for()
            page.locator('#wizard-from').fill('es-AR');page.locator('#wizard-to').fill('en-US')
            page.locator('#wizard-create').click();page.locator('.run-text').wait_for()
            project=server.store.list_projects()[0]['id']
            source=server.store.snapshot(project)['documents'][0]
            # Reported context, threshold persistence, decreases and conversation reset.
            page.evaluate("""() => {
              state.thread = 'context-test';
              const run = currentRuns().at(-1);
              run.context_thread = state.thread;
              run.context_usage = {tokens: 840, window: 1000};
              renderContextWarning();
            }""")
            assert page.locator('#context-warning').is_hidden()
            page.evaluate("() => {currentRuns().at(-1).context_usage.tokens=850;renderContextWarning()}")
            assert page.locator('#context-warning').is_visible()
            assert '85%' in page.locator('#context-warning').inner_text()
            page.evaluate("() => {$('context-warning-enabled').checked=false;$('context-warning-enabled').onchange()}")
            assert page.locator('#context-warning').is_hidden()
            assert page.evaluate("localStorage.getItem('sw-context-warning')") == 'false'
            page.evaluate("() => {$('context-warning-enabled').checked=true;$('context-warning-enabled').onchange();$('context-warning-threshold').value=90;$('context-warning-threshold').onchange()}")
            assert page.locator('#context-warning').is_hidden()
            assert page.evaluate("localStorage.getItem('sw-context-threshold')") == '90'
            page.evaluate("() => {currentRuns().at(-1).context_usage.tokens=950;renderContextWarning()}")
            assert page.locator('#context-warning').is_visible()
            page.evaluate("() => {currentRuns().at(-1).context_usage.tokens=200;renderContextWarning()}")
            assert page.locator('#context-warning').is_hidden()
            page.evaluate("() => {currentRuns().at(-1).context_usage.tokens=950;state.thread=null;renderContextWarning()}")
            assert page.locator('#context-warning').is_hidden()

            assert server.store.load(project)['translation_config']['source_language']=='es-AR'
            page.locator('#translation-next-start').wait_for()
            count = len(server.store.load(project)['runs'])
            prompt = page.locator('#prompt')
            prompt.fill('Mi criterio pendiente.')
            page.locator('#translation-next-start').click()
            assert prompt.input_value() == 'Mi criterio pendiente.'
            assert page.locator('#mode').input_value() == 'translate'
            assert len(server.store.load(project)['runs']) == count  # Preparing is not sending.
            prompt.fill('')
            page.locator('#translation-next-start').click()
            assert 'Continuemos la traducción' in prompt.input_value()
            prompt.fill('')
            compact = page.locator('.composer').bounding_box()['height']
            assert compact < 150, compact
            one = prompt.bounding_box()['height']
            assert one <= 36, one
            prompt.fill('\n'.join(['Texto']*7)); seven = prompt.bounding_box()['height']
            prompt.fill('\n'.join(['Texto']*20))
            assert prompt.bounding_box()['height'] == seven and seven > one * 3
            assert prompt.evaluate('el=>getComputedStyle(el).overflowY') == 'auto'
            prompt.evaluate('el=>el.scrollTop=60')
            page.evaluate('resizePrompt()')
            assert prompt.evaluate('el=>el.scrollTop') == 60
            prompt.fill('')
            assert prompt.bounding_box()['height'] == one
            page.set_viewport_size({'width':1920,'height':1080})
            page.wait_for_timeout(100)
            assert page.locator('#runs .run').first.bounding_box()['width'] > 1400
            heading = page.locator('.assistant-heading').bounding_box()
            tabs = page.locator('.assistant-tabs').bounding_box()
            assert tabs['x'] > heading['x'] + heading['width']
            assert page.locator('#connection').is_hidden()
            page.locator('#settings-open').click()
            import json
            version = json.loads((Path(__file__).resolve().parents[1]/'package.json').read_text())['version']
            assert page.locator('#app-version').inner_text() == 'Versión '+version
            page.locator('#settings-close').click()
            page.set_viewport_size({'width':1440,'height':1000})
            page.reload();page.locator('.run-text').wait_for()
            assert page.locator('#conversation-panel #purpose-banner, #conversation-panel #task-progress').count()==0
            assert page.locator('#purpose-banner').is_hidden() and page.locator('#task-progress').is_hidden()
            page.locator('[data-panel=notices]').click()
            assert page.locator('#notices-panel #purpose-banner').is_visible()
            assert 'Traducción con criterio del autor' in page.locator('#purpose-banner').inner_text()
            assert 'Listo para revisar' in page.locator('#notices-panel #task-progress').inner_text()
            assert page.locator('#task-progress progress').get_attribute('value')=='4'
            page.evaluate("notice('Prueba de limpieza')")
            page.locator('#notices-clear').click()
            assert page.locator('#purpose-banner').is_visible() and page.locator('#task-progress').is_visible()
            page.locator('[data-translation-setup]').click()
            page.locator('#translation-source').select_option(source['id'])
            page.locator('#translation-from').fill('es-AR');page.locator('#translation-to').fill('en-US')
            page.locator('#translation-intent').fill('Conservar el vínculo.')
            page.locator('#translation-form button[type=submit]').click()
            page.locator('#translation-dialog #notice-text').get_by_text('Encargo guardado. Marcá el original en las fuentes antes de traducir.',exact=True).wait_for()
            page.locator('#translation-start').click();page.locator('[data-criterion]').wait_for()
            assert len(server.store.snapshot(project)['documents'])==1
            page.locator('[data-nuance]').first.click();page.locator('[data-criterion]').fill('Afecto amistoso, sin romance.')
            page.reload();page.locator('[data-criterion]').wait_for()
            assert page.locator('[data-criterion]').input_value()=='Afecto amistoso, sin romance.'
            page.locator('[data-translation-answer]').click();page.locator('[data-translation-continue]').click()
            page.locator('[data-translation-text]').wait_for()
            assert len(server.store.snapshot(project)['documents'])==1
            page.locator('[data-translation-text]').fill('I care about you. — Revisado por el autor.')
            page.locator('[data-translation-accept]').click();page.locator('[data-open-translation]').wait_for()
            snapshot=server.store.snapshot(project);translated=next(d for d in snapshot['documents'] if d.get('translation'))
            assert translated['content'].endswith('Revisado por el autor.') and not translated['selected']
            assert server.store.document(server.store.load(project),source['id'])['content']=='Te quiero'
            page.locator('[data-open-translation]').click();page.locator('#editor').fill('I care about you. — Segunda revisión.')
            page.locator('#save').click();page.wait_for_function('()=>!dirty')
            page.locator('#translation-open').click();page.locator('#translation-documents summary').click()
            assert 'Por revisar' in page.locator('#translation-documents summary').inner_text()
            page.locator('[data-translation-review]').click()
            page.wait_for_function('()=>document.querySelector("#translation-status").textContent.startsWith("1 copias")')
            assert 'requiere otra revisión' not in page.locator('[data-open-translation]').locator('..').inner_text()
            with page.expect_download() as downloaded:page.locator('#translation-md').click()
            assert downloaded.value.suggested_filename=='traduccion.md'
            page.set_viewport_size({'width':390,'height':844});assert page.locator('#translation-dialog').evaluate('el=>el.scrollWidth<=el.clientWidth')
            page.screenshot(path='/tmp/story-workbench-translation.png',full_page=True)
            page.locator('#translation-close').click();page.set_viewport_size({'width':1440,'height':1000})
            page.locator('#settings-open').click();page.locator('#purpose').select_option('rpg');page.locator('#settings-close').click();page.wait_for_function('()=>state?.purpose==="rpg"')
            assert page.locator('#book-open').is_hidden() and page.locator('#plan-open').is_hidden()
            page.locator('[data-panel=notices]').click()
            page.locator('[data-rpg-starter]').click()
            assert page.locator('#prompt').is_visible() and page.locator('#prompt').evaluate('e=>e===document.activeElement')
            assert page.locator('#mode').input_value()=='draft'
            assert 'jugadores' in page.locator('#prompt').input_value()
            assert len(server.store.load(project)['documents'])==2
            assert page.locator('#template-type option[value=rpg_npc]').count()==1
            page.screenshot(path='/tmp/story-workbench-rpg.png',full_page=True)
            # Carpeta ficticia: selección, copia privada y ubicación persistente.
            folder=Path(directory)/'originales';folder.mkdir();(folder/'manuscript').mkdir()
            (folder/'manuscript'/'cuento.md').write_text('Un cuento de prueba.')
            (folder/'STYLE.md').write_text('Una voz ficticia.')
            (folder/'.env').write_text('not-a-real-key')
            page.locator('#settings-open').click();page.locator('#workspace-import').click()
            page.locator('#project-name').fill('Carpeta importada');page.locator('#wizard-next').click()
            page.locator('#wizard-folder-path').fill(str(folder));page.locator('#wizard-folder-scan').click()
            page.wait_for_function('()=>wizardFolder?.files.length===2')
            page.locator('#wizard-file-list input').nth(1).uncheck()
            page.locator('#wizard-create').click();page.wait_for_function('()=>state?.title==="Carpeta importada"')
            imported=server.store.snapshot(page.evaluate('state.id'))
            assert len(imported['documents'])==1 and imported['documents'][0]['name']=='manuscript/cuento.md'
            assert not imported['documents'][0]['selected']
            assert (folder/'manuscript'/'cuento.md').read_text()=='Un cuento de prueba.'
            page.locator('#settings-open').click()
            page.locator('#workspace-path').fill(str(folder));page.locator('#workspace-save').click()
            page.locator('#notice.error').wait_for();assert page.locator('#settings-dialog #notice').is_visible()
            page.locator('#notice-close').click()
            page.locator('#workspace-path').fill(directory);page.locator('#workspace-name').fill('Biblioteca nueva')
            page.locator('#workspace-save').click()
            page.wait_for_function('()=>workspaceInfo?.restart===true')
            assert (Path(directory)/'Biblioteca nueva'/'.story-workbench').is_file()
            page.reload();page.locator('#settings-open').click()
            page.wait_for_function('()=>workspaceInfo?.restart===true')
            assert page.locator('#workspace-path').input_value()==str(Path(directory)/'Biblioteca nueva')
            assert page.locator('#context-warning-threshold').input_value() == '90'
            assert page.locator('#context-warning-enabled').is_checked()
            page.locator('#workspace-default').click();page.wait_for_function('()=>workspaceInfo?.restart===false')
            page.locator('#settings-close').click()
            # Volver atrás, cambiar de modo y errores no deben crear proyectos vacíos.
            count=len(server.store.list_projects());page.locator('#new-project').click()
            page.locator('#project-name').fill('No crear');page.locator('#wizard-next').click()
            page.locator('#wizard-purpose').select_option('translation')
            page.locator('#wizard-back').click();page.locator('#wizard-next').click()
            page.locator('#wizard-file').set_input_files(dict(name='Idioma.txt',mimeType='text/plain',buffer='Ella estaba en la casa cuando él dijo que sus amigos habían pasado por el jardín, pero no había una carta para los niños.'.encode()))
            page.wait_for_function('()=>document.querySelector("#wizard-from").value==="Español"')
            page.set_viewport_size({'width':390,'height':844})
            assert page.locator('#project-wizard').evaluate('el=>el.scrollWidth<=el.clientWidth')
            page.emulate_media(reduced_motion='reduce')
            page.screenshot(path='/tmp/story-workbench-translation-wizard.png')
            page.set_viewport_size({'width':1440,'height':1000})
            page.locator('#wizard-to').fill('Español');page.locator('#wizard-create').click()
            page.locator('#project-wizard #notice.error').wait_for()
            assert len(server.store.list_projects())==count
            page.locator('#wizard-purpose').select_option('novel');assert page.locator('#wizard-story').is_visible()
            page.locator('#wizard-cancel').click();assert len(server.store.list_projects())==count
            assert not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK modos UI: wizard, encargo, matiz, criterio recuperable, aprobación separada, revisión por versión, exportación, rol, carpeta importada sin cambiar originales, espacio persistente y wizard compacto.')
