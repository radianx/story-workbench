"""Recorrido real del navegador con material ficticio. Requiere Playwright solo para comprobar."""
import json
from pathlib import Path
import sys
import tempfile
import threading
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright


def main():
    with tempfile.TemporaryDirectory(prefix='sw-browser-') as directory:
        server=AppServer(0,directory)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(server.origin+'/#token='+server.token)
                page.get_by_role('button',name='Explorar un proyecto ficticio').click()
                page.locator('#editor').wait_for()
                page.wait_for_function("() => document.querySelector('#editor').value.includes('llave azul')")
                project=server.store.list_projects()[0]['id']
                data=server.store.snapshot(project);doc=data['documents'][0]
                original=page.locator('#editor').input_value()
                page.locator('#editor').fill(original+'\nUna línea nueva.')
                page.get_by_role('button',name='Guardar',exact=False).last.click()
                page.wait_for_function("() => document.querySelector('#save-state').textContent==='Guardado local'")
                page.get_by_role('tab',name='Historial',exact=True).click()
                page.get_by_role('button',name='Restaurar',exact=True).wait_for()
                page.on('dialog',lambda dialog:dialog.accept())
                page.get_by_role('button',name='Restaurar',exact=True).click()
                page.get_by_role('tab',name='Escribir',exact=True).click()
                page.wait_for_function("() => !document.querySelector('#editor').value.includes('Una línea nueva')")
                # Cambios externos no pisan el borrador.
                page.locator('#editor').fill(original+'\nBorrador privado.')
                path=server.store.path(project,'documents',doc['id']+'.md')
                path.write_text(original+'\nEdición externa.',encoding='utf-8')
                page.locator('#save').click();page.locator('#conflict').wait_for()
                assert 'Borrador privado' in page.locator('#editor').input_value()
                assert 'Edición externa' in path.read_text()
                page.locator('#reload').click()
                page.wait_for_function("() => document.querySelector('#editor').value.includes('Edición externa')")
                # Una respuesta de prueba nunca se aplica al insertarse en el registro.
                with server.store.lock:
                    data=server.store.load(project);current=server.store.document(data,doc['id'])
                    run={'id':'browser-test','source_texts':{doc['id']:current['content']}}
                    server.store.proposals_from_result(data,run,[dict(document_id=doc['id'],before='llave azul',after='llave roja',reason='Coincidir con canon.')])
                    server.store.persist(data)
                assert 'llave azul' in path.read_text()
                page.get_by_role('tab',name='Propuestas').click()
                page.get_by_role('button',name='Aceptar bloque').wait_for(timeout=10000)
                page.get_by_role('button',name='Aceptar bloque').click()
                page.wait_for_function("() => document.querySelector('#editor').value.includes('llave roja')")
                assert 'llave roja' in path.read_text()
                page.get_by_role('tab',name='Decisiones',exact=True).click()
                page.locator('#decision-text').fill('Conservar incierto el origen de la radio.')
                page.get_by_role('button',name='Registrar',exact=True).click()
                page.get_by_text('Conservar incierto el origen de la radio.',exact=True).wait_for()
                # Importación de copia y vista previa sin ejecución HTML.
                page.locator('#files').set_input_files({'name':'Referencia ficticia.md','mimeType':'text/markdown','buffer':b'# Fuente\n\n<script>window.injected=true</script>'})
                page.get_by_role('button',name='Referencia ficticia').wait_for()
                page.get_by_role('button',name='Referencia ficticia').click()
                page.get_by_role('tab',name='Vista previa',exact=True).click()
                assert not page.evaluate('Boolean(window.injected)')
                assert '<script>' in page.locator('#preview').inner_text()
                page.get_by_role('button',name='01 · La última luz').click()
                page.get_by_role('tab',name='Escribir',exact=True).click()
                page.get_by_role('tab',name='Conversación',exact=True).click()
                page.locator('#focus').click();assert not page.locator('.sources').is_visible()
                page.locator('#focus').click();assert page.locator('.sources').is_visible()
                with page.expect_download() as download:
                    page.locator('#export').click()
                assert download.value.suggested_filename=='story-workbench.zip'
                page.screenshot(path='/tmp/story-workbench-mvp.png',full_page=True)
                page.reload();page.wait_for_function("() => document.querySelector('#editor').value.includes('llave roja')")
                # Cambio de proyecto: ni fuentes ni decisiones del anterior.
                page.locator('#new-project').click();page.locator('#new-name').fill('Otro universo')
                page.locator('#name-dialog button[value=ok]').click()
                page.wait_for_function("() => document.querySelector('#project-title').textContent==='Otro universo'")
                assert 'La última luz' not in page.locator('#documents').inner_text()
                assert 'Conservar incierto' not in page.locator('#decisions').inner_text()
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert errors==[],errors
                browser.close()
                print('OK navegador: edición, historial, conflicto, propuesta, decisión, importación segura, foco, exportación, recarga y aislamiento de proyectos.')
        finally:
            server.shutdown();server.server_close()


if __name__=='__main__':main()
