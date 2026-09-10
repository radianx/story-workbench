"""Temas compartibles y archivo reversible con proyectos ficticios; sin servicios IA."""
import json,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory(prefix='sw-themes-archive-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out')
    project=server.store.create('Archivo ficticio',True)['id']
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.emulate_media(reduced_motion='reduce')
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.locator('#settings-open').click()
            page.locator('#theme').select_option('light:custom')
            assert page.locator('#theme').input_value()=='light:custom' and page.evaluate("!!customTheme('light')")
            assert page.locator('#app-font option').count()==5
            families=[]
            for font in ['system','arial','georgia','times','mono']:
                page.locator('#app-font').select_option(font)
                families.append(page.locator('body').evaluate('e=>getComputedStyle(e).fontFamily'))
                for selector in ['#prompt','#editor','#send','.assistant-heading h2']:
                    assert page.locator(selector).evaluate('e=>getComputedStyle(e).fontFamily')==families[-1]
            assert len(set(families))==5
            assert page.locator('#theme').evaluate("e=>Math.abs(e.getBoundingClientRect().width-document.querySelector('#appearance-controls').getBoundingClientRect().width)<2")
            def check_material():
                assert page.evaluate('''()=>{
                    const probe=document.createElement('span');document.body.append(probe);
                    const expected=key=>{probe.style.color='var(--'+key+')';return getComputedStyle(probe).color};
                    const checks=[['.manuscript','backgroundColor','paper'],['.editor-footer','backgroundColor','paper'],['.editor-footer','color','muted'],['.editor-toolbar','borderTopColor','line'],['.editor-meta select','color','green'],['.tab.active','color','green'],['.breadcrumb','color','muted']];
                    const valid=checks.every(([selector,property,key])=>getComputedStyle(document.querySelector(selector))[property]===expected(key));probe.remove();return valid;
                }''')
            accents=[]
            for theme in ('light:neon','dark:neon','light:vice','dark:vice'):
                page.locator('#theme').select_option(theme)
                check_material()
                accents.append(page.locator('#send').evaluate('e=>getComputedStyle(e).backgroundColor'))
            assert len(set(accents))==4,accents
            page.locator('#custom-theme-controls summary').click();page.locator('#theme-customize').click()
            assert page.locator('#theme').input_value()=='dark:custom'
            page.locator('#custom-theme-name').fill('Mi tema de prueba')
            page.locator('[data-theme-color=green]').fill('#ff8800')
            page.locator('#background-opacity').fill('42');page.locator('#background-opacity').dispatch_event('input')
            assert page.locator('#ambient-image').evaluate('e=>getComputedStyle(e).opacity')=='0.42'
            with page.expect_download() as result:page.locator('#theme-export').click()
            exported=json.loads(Path(result.value.path()).read_text());assert exported['name']=='Mi tema de prueba' and exported['colors']['green']=='#ff8800' and exported['backgroundOpacity']==42
            page.locator('#theme-reset').click();assert page.locator('#theme').input_value()=='dark'
            page.locator('#theme-file').set_input_files(dict(name='theme.json',mimeType='application/json',buffer=json.dumps(exported).encode()))
            page.wait_for_function("()=>$('theme').value==='dark:custom'")
            check_material()
            before=page.evaluate("localStorage.getItem('sw-custom-dark')")
            bad=dict(exported,colors=dict(exported['colors'],bg='url(https://invalid.test/track)'))
            page.locator('#theme-file').set_input_files(dict(name='bad.json',mimeType='application/json',buffer=json.dumps(bad).encode()))
            page.wait_for_function("()=>$('notice-text').textContent.includes('#RRGGBB')")
            assert page.evaluate("localStorage.getItem('sw-custom-dark')")==before
            page.locator('#notice-close').click();page.locator('#settings-close').click();page.reload();page.locator('#workspace').wait_for()
            assert page.locator('#app-font').input_value()=='mono'
            assert page.locator('body').evaluate('e=>getComputedStyle(e).fontFamily')==families[-1]
            assert page.locator('#theme').input_value()=='dark:custom'
            assert page.locator('#send').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(255, 136, 0)'
            assert page.locator('#background-opacity').input_value()=='42'
            page.locator('#settings-open').click();page.set_viewport_size({'width':390,'height':844})
            page.locator('#custom-theme-controls summary').click()
            assert page.locator('#settings-dialog').evaluate('e=>e.scrollWidth<=e.clientWidth')
            assert page.locator('#theme').evaluate("e=>Math.abs(e.getBoundingClientRect().width-document.querySelector('#appearance-controls').getBoundingClientRect().width)<2")
            page.screenshot(path='/tmp/sw-custom-theme-mobile.png')
            page.locator('#settings-close').click();page.set_viewport_size({'width':1440,'height':1000})
            page.evaluate("state.workflow='guided';applyWorkflow()")
            page.locator('#material-toggle').click();assert page.locator('.manuscript').is_visible();check_material()
            page.screenshot(path='/tmp/sw-material-custom-theme.png')
            page.evaluate("state.workflow='writing';applyWorkflow()")
            # No permite ocultar un documento con cambios sin guardar.
            original=page.locator('#editor').input_value();page.locator('#editor').fill(original+'\nUna prueba.');page.locator('#archive-project').click()
            page.wait_for_function("()=>$('notice-text').textContent.includes('Guardá los cambios')")
            assert server.store.list_projects()[0]['id']==project
            page.locator('#notice-close').click();page.locator('#save').click();page.wait_for_function('()=>!dirty')
            files={f.relative_to(server.store.root):f.read_bytes() for f in server.store.root.rglob('*') if f.is_file() and f.name!='project.json'}
            page.locator('#prompt').fill('Mensaje sin enviar')
            page.locator('#archive-project').focus();page.keyboard.press('Enter');page.locator('#welcome').wait_for()
            assert server.store.list_projects()==[]
            page.reload();page.locator('#welcome').wait_for();page.locator('#welcome [data-archived-open]').click()
            page.locator('[data-restore-project]').click();page.locator('#workspace').wait_for()
            assert page.locator('#prompt').input_value()=='Mensaje sin enviar'
            assert page.locator('#editor').input_value()==original+'\nUna prueba.'
            assert not server.store.load(project)['runs']
            assert files=={f.relative_to(server.store.root):f.read_bytes() for f in server.store.root.rglob('*') if f.is_file() and f.name!='project.json'}
            page.evaluate("localStorage.setItem('sw-font','unknown-font')");page.reload();page.locator('#workspace').wait_for()
            assert page.locator('#app-font').input_value()=='system'
            assert not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK temas y material, selector de ancho completo, cinco tipografías locales persistidas y fallback, JSON validado, opacidad, móvil y archivo/restauración.')
