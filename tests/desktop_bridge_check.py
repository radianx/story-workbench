"""Frontend desktop save/cancel/error and close guards; no real files, accounts or providers."""
import sys, tempfile, threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-desktop-bridge-') as directory:
    server=AppServer(0,directory)
    server.store.create('Ficción de exportación',True)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page()
            page.add_init_script("window.storyDesktop=true;localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            saves=[];closes=[]
            def save(route):
                saves.append(route.request.post_data)
                assert route.request.headers['authorization']=='Bearer '+server.token
                route.fulfill(content_type='application/json',body='{"saved":true}')
            page.route('**/api/desktop/save?*',save)
            assert page.evaluate("()=>download(new Blob(['Ficción de prueba']),'libro.md')") is True
            assert saves==['Ficción de prueba']
            page.unroute('**/api/desktop/save?*')
            page.route('**/api/desktop/save?*',lambda route:route.fulfill(content_type='application/json',body='{"saved":false}'))
            assert page.evaluate("()=>download(new Blob(['cancelar']),'libro.md')") is False
            page.unroute('**/api/desktop/save?*')
            page.route('**/api/desktop/save?*',lambda route:route.fulfill(status=500,content_type='application/json',body='{"error":"Destino no disponible"}'))
            page.locator('#download').click()
            page.wait_for_function("()=>$('notice-text').textContent==='Destino no disponible'")
            def close(route):
                closes.append(True);route.fulfill(content_type='application/json',body='{"ok":true}')
            page.route('**/api/desktop/close',close)
            page.evaluate('dirty=true')
            page.once('dialog',lambda dialog:dialog.dismiss())
            page.evaluate('()=>storyRequestClose()');assert not closes
            page.once('dialog',lambda dialog:dialog.accept())
            page.evaluate('()=>storyRequestClose()');assert len(closes)==1
            page.evaluate("dirty=false;state.runs.push({status:'running'})")
            page.once('dialog',lambda dialog:dialog.dismiss())
            page.evaluate('()=>storyRequestClose()');assert len(closes)==1
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK escritorio: guardar/cancelar/error visible; cierre cancelable con borrador o tarea en curso.')
