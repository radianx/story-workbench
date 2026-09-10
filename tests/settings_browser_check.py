"""Paletas, distribución y giro 3D con ficción temporal; sin IA ni datos privados."""
from pathlib import Path
import sys,tempfile,threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory(prefix='sw-settings-') as temp:
    server=AppServer(0,temp);server.account.set(status='signed_out');project=server.store.create('Diseño ficticio',True);data=server.store.load(project['id']);data['workflow']='guided';data['runs']=[dict(id='test',mode='interview',prompt='Ficción',text='¿Qué historia querés crear?',status='completed',sources=[],date=0)];server.store.persist(data)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1920,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.emulate_media(reduced_motion='reduce') # Medir colores finales; movimiento se comprueba por separado.
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            page.locator('#settings-open').click();assert page.locator('#settings-dialog').bounding_box()['width']>950
            assert page.locator('#appearance-controls select').count()==1 and page.locator('.local-badge').count()==0
            for mode,values in [('light',['sky','cream','pink']),('dark',['violet','red','blue'])]:
                page.locator('#theme').select_option(mode);colors=[]
                for value in values:
                    page.locator('#theme').select_option(mode+':'+value);page.wait_for_timeout(200)
                    colors.append(page.locator('#send').evaluate('(e)=>getComputedStyle(e).backgroundColor'))
                    assert page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')==('rgb(247, 248, 250)' if mode=='light' else 'rgb(9, 9, 12)')
                assert len(set(colors))==3,colors
            page.locator('#theme').select_option('system');page.locator('#settings-close').click();page.reload();page.locator('#workspace').wait_for()
            assert page.evaluate("document.documentElement.dataset.lightPalette==='pink' && document.documentElement.dataset.darkPalette==='blue'")
            page.emulate_media(color_scheme='dark');assert page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(9, 9, 12)'
            page.emulate_media(color_scheme='light');assert page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(247, 248, 250)'
            page.wait_for_function('()=>document.querySelector("#account-open").dataset.status==="signed_out"');assert page.locator('#account-open').inner_text()=='ChatGPT' and len(page.locator('#account-open').get_attribute('aria-label'))>8
            page.locator('#theme-toggle').click();assert page.locator('#theme').input_value()=='dark:blue'
            prompt=page.locator('#prompt').bounding_box();assert prompt['width']>1000
            assert page.locator('#runs').bounding_box()['height']>page.locator('.composer').bounding_box()['height']*2
            assert page.locator('.composer-bottom #ai-model').is_visible() and page.locator('#dictate').is_visible()
            page.locator('#help-open').click();assert page.locator('#help-dialog').bounding_box()['width']>1100;page.locator('#help-close').click()
            page.locator('#book-open').click();stage=page.locator('#book-stage').bounding_box();before=page.locator('#book-rotation').input_value()
            page.mouse.move(stage['x']+stage['width']/2,stage['y']+stage['height']/2);page.mouse.down();page.mouse.move(stage['x']+stage['width']/2+80,stage['y']+stage['height']/2+20,steps=5);page.mouse.up()
            assert page.locator('#book-rotation').input_value()!=before
            before=int(page.locator('#book-rotation').input_value());page.locator('#book-stage').focus();page.keyboard.press('ArrowRight');assert int(page.locator('#book-rotation').input_value())==before+10
            assert page.evaluate('!bookDirty');page.locator('#book-close').click()
            page.screenshot(path='/tmp/story-workbench-settings-dark.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844});page.locator('#settings-open').click()
            assert page.locator('#settings-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
            page.locator('#realtime-settings').click();assert page.locator('#realtime-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
            assert page.locator('#realtime-remember').is_disabled();page.locator('#realtime-close').click();page.locator('#settings-close').click()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('#prompt').bounding_box()['y']<844
            assert not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK configuración: seis paletas, persistencia/sistema, chat amplio, modales adaptables, estado accesible y giro 3D por mouse/teclado.')
