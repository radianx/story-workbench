"""Primera apertura, teclado, navegación oral y grosor físico con ficción; sin servicios IA."""
from pathlib import Path
import sys,tempfile,threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory(prefix='sw-setup-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out');project=server.store.create('Historia ficticia',True)
    doc=server.store.add_document(project['id'],'Libro.md','manuscrito','palabra '*30000)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(server.origin+'/#token='+server.token);page.locator('#setup-dialog').wait_for()
            assert not page.locator('#workspace').is_visible()
            assert page.locator('#setup-progress').inner_text()=='Paso 1 de 4'
            assert page.locator('#setup-appearance #theme').input_value()=='system'
            page.locator('#theme').select_option('light:pink');page.locator('#theme').select_option('dark:violet')
            assert page.evaluate("document.documentElement.dataset.darkPalette==='violet' && localStorage.getItem('sw-theme')==='dark'")
            page.locator('#theme').select_option('system');page.emulate_media(color_scheme='light')
            light=page.evaluate('getComputedStyle(document.body).backgroundColor')
            page.emulate_media(color_scheme='dark');assert page.evaluate('getComputedStyle(document.body).backgroundColor')!=light
            page.locator('#theme').select_option('dark:violet')
            page.locator('#setup-next').focus();page.keyboard.press('Enter');assert '2 de 4' in page.locator('#setup-progress').inner_text()
            page.locator('#setup-account').focus();page.keyboard.press('Enter');page.locator('#account-dialog').wait_for();page.keyboard.press('Escape')
            page.locator('#setup-next').focus();page.keyboard.press('Enter');assert '3 de 4' in page.locator('#setup-progress').inner_text()
            page.locator('#setup-voice').focus();page.keyboard.press('Enter');page.locator('#realtime-dialog').wait_for()
            # Regresión: voz está antes que setup en el DOM, pero encima en la capa modal.
            page.locator('#realtime-save').click();page.locator('#notice').wait_for()
            assert 'Confirmá el envío' in page.locator('#notice-text').inner_text()
            assert page.locator('#notice').get_attribute('role')=='alert'
            assert page.locator('#notice').get_attribute('aria-live')=='assertive'
            for width in (1440,390):
                page.set_viewport_size({'width':width,'height':844})
                assert page.locator('#notice').evaluate("e=>e.parentElement.id==='realtime-dialog' && e.contains(document.elementFromPoint(e.getBoundingClientRect().x+20,e.getBoundingClientRect().y+20))")
                box=page.locator('#notice').bounding_box();assert box['y']>=0 and box['y']+box['height']<=844
                page.screenshot(path=f'/tmp/story-workbench-setup-error-{width}.png')
            page.set_viewport_size({'width':1440,'height':1000})
            page.evaluate("navigateWorkbench('back')")
            assert page.locator('#setup-dialog').is_visible() and not page.locator('#realtime-dialog').is_visible()
            page.wait_for_function("()=>$('notice').parentElement.id==='setup-dialog'")
            page.locator('#notice-close').click()
            page.keyboard.press('Escape');page.locator('#workspace').wait_for();assert page.evaluate("localStorage.getItem('sw-setup-seen')")=='1'
            page.reload();page.locator('#workspace').wait_for();assert not page.locator('#setup-dialog').is_visible()
            assert page.locator('#theme').input_value()=='dark:violet' and page.evaluate("document.documentElement.dataset.lightPalette==='pink'")
            assert page.locator('#appearance-controls').evaluate("e=>e.parentElement.id==='settings-general'")
            assert page.locator('#theme').count()==1
            page.keyboard.press('Control+,');page.locator('#setup-open').focus();page.keyboard.press('Enter');page.locator('#setup-dialog').wait_for()
            page.locator('#setup-next').click();page.locator('#setup-next').click();page.locator('#setup-next').click();page.locator('#setup-resume').focus();page.keyboard.press('Enter');page.locator('#workspace').wait_for()
            page.keyboard.press('Control+k');page.locator('#navigation-search').fill('material');page.keyboard.press('Enter');assert page.locator('#editor').evaluate('e=>e===document.activeElement')
            page.keyboard.press('Control+k');page.locator('#navigation-search').fill('propuestas');page.keyboard.press('Enter');page.locator('[data-panel=proposals]').focus();page.keyboard.press('ArrowRight');assert page.locator('[data-panel=decisions]').get_attribute('aria-selected')=='true'
            # Misma allowlist que usa la voz: jamás ejecuta un selector arbitrario.
            page.evaluate("navigateWorkbench('settings')");page.locator('#settings-dialog').wait_for();page.keyboard.press('Escape')
            assert page.evaluate("navigateWorkbench('delete').then(()=>false,()=>true)")
            page.keyboard.press('Control+k');page.locator('#navigation-search').fill('libro');page.keyboard.press('Enter');page.locator('#book-dialog').wait_for()
            assert page.locator('#book-width').input_value()=='152.4' and page.locator('#book-height').input_value()=='228.6'
            pages=int(page.locator('#book-pages').input_value());assert 100<=pages<=110
            spine=float(page.locator('#book-thickness').input_value());assert abs(spine-pages*.0572)<.006
            page.locator('#book-width').fill('127');assert int(page.locator('#book-pages').input_value())>pages
            page.locator('#book-default-size').click();assert int(page.locator('#book-pages').input_value())==pages
            page.locator('#book-sizing').select_option('pages');page.locator('#book-pages').fill('300');page.locator('#book-paper').select_option('cream');assert page.locator('#book-thickness').input_value()=='19.05'
            page.locator('#book-save').click();page.wait_for_function("()=>!bookDirty")
            assert server.store.load(project['id'])['production']['spine']==19.05
            page.locator('#book-close').click();page.reload();page.locator('#book-open:not([disabled])').click();assert page.locator('#book-pages').input_value()=='300' and page.locator('#book-paper').input_value()=='cream'
            page.locator('#book-close').click()
            # Antigua maqueta: el valor manual no cambia al migrar.
            data=server.store.load(project['id']);data['production']={'width':140,'height':210,'spine':32};server.store.persist(data)
            page.reload();page.locator('#book-open:not([disabled])').click();assert page.locator('#book-sizing').input_value()=='manual' and page.locator('#book-thickness').input_value()=='32';page.locator('#book-close').click()
            page.set_viewport_size({'width':390,'height':844});page.locator('#settings-open').click();page.locator('#setup-open').click();assert page.locator('#setup-dialog').evaluate('e=>e.scrollWidth<=e.clientWidth')
            page.screenshot(path='/tmp/story-workbench-setup.png',full_page=True)
            assert not errors,errors
            assert not server.store.load(project['id'])['runs']
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK setup: tema primero y persistente, avisos sobre diálogo anidado en escritorio/móvil, primera apertura, omitir/reabrir, cuenta/voz opcionales, teclado, destinos compartidos y libro por páginas/papel/tamaño, persistencia y migración manual.')
