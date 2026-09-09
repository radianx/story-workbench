"""Modos y revisión humana con respuestas ficticias; sin llamadas IA."""
import sys
from pathlib import Path
import tempfile
import threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from workbench_modes import validate_translation
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
            page.locator('#wizard-create').click();page.locator('.run-text').wait_for()
            project=server.store.list_projects()[0]['id']
            source=server.store.add_document(project,'Original','manuscrito','Te quiero')
            page.reload();page.locator('#translation-open').click()
            page.locator('#translation-source').select_option(source['id'])
            page.locator('#translation-from').fill('es-AR');page.locator('#translation-to').fill('en-US')
            page.locator('#translation-intent').fill('Conservar el vínculo.')
            page.locator('#translation-form button[type=submit]').click()
            page.get_by_text('Encargo guardado. Marcá el original en las fuentes antes de traducir.',exact=True).wait_for()
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
            page.locator('[data-rpg-starter]').click();assert page.locator('#mode').input_value()=='draft'
            assert 'jugadores' in page.locator('#prompt').input_value()
            assert len(server.store.load(project)['documents'])==2
            assert page.locator('#template-type option[value=rpg_npc]').count()==1
            page.screenshot(path='/tmp/story-workbench-rpg.png',full_page=True)
            assert not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK modos UI: wizard, encargo, matiz, criterio recuperable, aprobación separada, revisión por versión, exportación, rol y vista compacta.')
