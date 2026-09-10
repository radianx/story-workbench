"""Preferencias antes del pintado y feedback de acciones, sin IA ni datos privados."""
from pathlib import Path
import sys,tempfile,threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory(prefix='sw-motion-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out');server.store.create('Ficción de interfaz',True)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.locator('#settings-open').click();page.locator('#theme').select_option('light:pink');page.locator('#theme').select_option('dark:violet');page.locator('#settings-close').click()
            held=[];page.route('**/app.js',lambda route:held.append(route))
            page.reload(wait_until='commit')
            page.wait_for_function('()=>document.documentElement.dataset.darkPalette==="violet"')
            assert page.evaluate('document.documentElement.dataset.theme')=='dark'
            assert page.evaluate('typeof applyTheme')=='undefined' # Preferencia restaurada antes del JS principal.
            page.wait_for_function('()=>!!document.body')
            assert page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(9, 9, 12)'
            for route in held:route.continue_()
            page.unroute('**/app.js');page.locator('#workspace').wait_for()
            # Una acción de guardado pendiente no se repite con teclado/clic.
            # El wrapper común mantiene feedback incluso antes de recibir respuesta.
            page.evaluate("()=>{window.clicks=0;document.querySelector('#save').disabled=false;document.querySelector('#save').onclick=action(()=>{clicks++;return new Promise(resolve=>window.finishAction=resolve)})}")
            page.locator('#save').click();assert page.locator('#save').get_attribute('aria-busy')=='true'
            page.evaluate("document.querySelector('#save').click()");assert page.evaluate('clicks')==1
            assert page.locator('#save').evaluate("e=>getComputedStyle(e,'::after').animationName")=='workbench-wait'
            page.evaluate('finishAction()');page.wait_for_function('()=>!document.querySelector("#save").hasAttribute("aria-busy")')
            page.evaluate("()=>{document.querySelector('#save').onclick=action(async()=>{throw new Error('Fallo ficticio')});document.querySelector('#save').click()}")
            page.locator('[data-panel=notices]').click();page.locator('#notices-list').get_by_text('Fallo ficticio',exact=True).wait_for();assert page.locator('#save').get_attribute('aria-busy') is None;page.locator('[data-panel=conversation]').click()
            # Repetir un formulario ocupado tampoco permite la navegación nativa.
            page.evaluate("()=>{window.formCalls=0;const form=document.querySelector('#decision-form'),button=form.querySelector('button');form.onsubmit=action(e=>{e.preventDefault();formCalls++;return new Promise(resolve=>window.finishForm=resolve)});window.submitOnce=()=>form.dispatchEvent(new SubmitEvent('submit',{bubbles:true,cancelable:true,submitter:button}));}")
            assert page.evaluate('submitOnce()') is False
            assert page.evaluate('submitOnce()') is False and page.evaluate('formCalls')==1
            page.evaluate('finishForm()')
            # Los cambios de etapa conservan el elemento; una actualización no reanima el texto.
            page.evaluate("()=>{state.runs=[{id:'motion',mode:'chat',status:'running',stage:'generation'}];renderProgress();window.progressElement=document.querySelector('#task-progress progress');state.runs[0].status='completed';renderProgress()}")
            assert page.evaluate('document.querySelector("#task-progress progress")===progressElement')
            assert page.locator('#task-progress').evaluate("e=>getComputedStyle(e).animationName")=='workbench-ready'
            page.evaluate('renderProgress()');assert not page.locator('#task-progress').evaluate("e=>e.classList.contains('just-completed')")
            page.locator('#settings-open').click();assert page.locator('#settings-dialog').evaluate('e=>getComputedStyle(e).animationName')=='workbench-enter'
            page.emulate_media(reduced_motion='reduce')
            assert page.locator('#settings-dialog').evaluate('e=>getComputedStyle(e).animationName')=='none'
            page.locator('#settings-close').click();page.locator('#book-open').click()
            stage=page.locator('#book-stage');assert page.locator('#book-model').evaluate('e=>getComputedStyle(e).transitionDuration')=='0s'
            page.emulate_media(reduced_motion='no-preference')
            box=stage.bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.down()
            assert page.locator('#book-model').evaluate('e=>getComputedStyle(e).transitionDuration')=='0s'
            page.mouse.up();assert page.locator('#book-model').evaluate('e=>getComputedStyle(e).transitionDuration')!='0s'
            page.locator('#book-close').click()
            # Preferencias inválidas vuelven al sistema sin romper la UI.
            page.evaluate("localStorage.setItem('sw-theme','invalid');localStorage.setItem('sw-palette-dark','invalid')");page.reload();page.locator('#workspace').wait_for()
            assert page.locator('#theme').input_value()=='system' and page.evaluate("document.documentElement.dataset.darkPalette==='sage'")
            assert not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK microinteracciones: tema antes del pintado, espera sin doble acción, recuperación de error, progreso estable, diálogos y movimiento reducido, 3D directo.')
