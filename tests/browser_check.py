"""Recorrido real del navegador con material ficticio. Requiere Playwright solo para comprobar."""
import json
from pathlib import Path
import sys
import tempfile
import threading
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import AppServer
from test_desktop_features import MODELS
from playwright.sync_api import sync_playwright


def main():
    with tempfile.TemporaryDirectory(prefix='sw-browser-') as directory:
        server=AppServer(0,directory)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        server.account.set(status='connected',models=MODELS) # Auth protocol has a separate executable test.
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.emulate_media(color_scheme='dark')
                page.goto(server.origin+'/#token='+server.token)
                theme=page.get_by_role('combobox',name='Tema de apariencia')
                assert theme.input_value()=='system'
                assert page.locator('body').evaluate('(el) => getComputedStyle(el).backgroundColor')=='rgb(21, 28, 24)'
                page.emulate_media(color_scheme='light')
                assert page.locator('body').evaluate('(el) => getComputedStyle(el).backgroundColor')=='rgb(245, 246, 241)'
                theme.select_option('dark')
                assert page.locator('body').evaluate('(el) => getComputedStyle(el).backgroundColor')=='rgb(21, 28, 24)'
                page.reload()
                assert theme.input_value()=='dark'
                theme.select_option('light')
                page.emulate_media(color_scheme='dark')
                assert page.locator('body').evaluate('(el) => getComputedStyle(el).backgroundColor')=='rgb(245, 246, 241)'
                theme.select_option('system')
                assert page.evaluate("localStorage.getItem('sw-theme')") is None
                assert page.locator('body').evaluate('(el) => getComputedStyle(el).backgroundColor')=='rgb(21, 28, 24)'
                page.get_by_role('button',name='Explorar un proyecto ficticio').click()
                page.locator('#editor').wait_for()
                page.wait_for_function("() => document.querySelector('#editor').value.includes('llave azul')")
                page.screenshot(path='/tmp/story-workbench-dark.png',full_page=True)
                project=server.store.list_projects()[0]['id']
                data=server.store.snapshot(project);doc=data['documents'][0]
                page.locator('#ai-model:not([disabled])').wait_for()
                assert page.locator('#ai-model').input_value()=='modelo-a'
                page.locator('#ai-effort').select_option('high')
                page.wait_for_function("() => !document.querySelector('#ai-effort').disabled")
                assert server.store.load(project)['ai_preferences']=={'model':'modelo-a','effort':'high'}
                page.locator('#ai-model').select_option('modelo-b')
                page.wait_for_function("() => document.querySelector('#ai-effort').value==='low'")
                assert page.locator('#ai-effort option').count()==1
                page.reload();page.wait_for_function("() => document.querySelector('#ai-model').value==='modelo-b'")
                assert page.locator('#ai-effort').input_value()=='low'
                # Undo/redo nativo: texto, guardado, formato y aislamiento entre documentos.
                editor=page.locator('#editor');before_undo=editor.input_value()
                editor.focus();editor.press('Control+End');editor.press_sequentially('X')
                page.locator('#undo').click();assert editor.input_value()==before_undo, repr(editor.input_value())
                page.locator('#redo').click();assert editor.input_value()==before_undo+'X'
                page.locator('#save').click()
                page.wait_for_function("() => document.querySelector('#save-state').textContent==='Guardado local'")
                editor.focus();editor.press('Control+z');assert editor.input_value()==before_undo
                editor.press('Control+Shift+z');assert editor.input_value()==before_undo+'X'
                page.locator('#undo').click()
                page.locator('#save').click()
                page.wait_for_function("() => document.querySelector('#save-state').textContent==='Guardado local'")
                editor.evaluate('(e)=>{e.focus();e.setSelectionRange(0,2)}')
                page.get_by_role('button',name='Negrita',exact=True).click()
                assert editor.input_value().startswith('**# **')
                page.locator('#undo').click();assert editor.input_value()==before_undo
                page.get_by_role('button',name='Canon del faro').click()
                canon_before=editor.input_value();page.locator('#undo').click();assert editor.input_value()==canon_before
                page.get_by_role('button',name='01 · La última luz').click()
                original=page.locator('#editor').input_value()
                page.locator('#editor').fill(original+'\nUna línea nueva.')
                page.get_by_role('button',name='Guardar',exact=False).last.click()
                page.wait_for_function("() => document.querySelector('#save-state').textContent==='Guardado local'")
                page.get_by_role('tab',name='Historial',exact=True).click()
                page.get_by_role('button',name='Restaurar',exact=True).first.wait_for()
                page.on('dialog',lambda dialog:dialog.accept())
                page.get_by_role('button',name='Restaurar',exact=True).first.click()
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
                # Plan: orden real, meta, revisión vinculada a la versión y exportación del libro.
                page.locator('#plan-open').click()
                page.locator('#word-goal').fill('80000');page.locator('#goal-form button').click()
                page.get_by_text('Meta guardada.',exact=True).wait_for()
                card=page.locator('.plan-card').first
                card.locator('[name=synopsis]').fill('Inés escucha una voz imposible.')
                card.locator('[name=pov]').fill('Inés')
                card.locator('[name=stage]').select_option('reviewed')
                card.get_by_role('button',name='Guardar ficha',exact=True).click()
                card.get_by_text('Ficha guardada.',exact=True).wait_for()
                assert '1 de 2' in page.locator('#plan-progress').inner_text()
                card.locator('[data-move="1"]').click()
                page.wait_for_function("() => document.querySelector('.plan-card strong').textContent.includes('El cuarto de radio')")
                with page.expect_download() as exported:page.locator('#book-docx').click()
                assert exported.value.suggested_filename=='libro.docx'
                page.screenshot(path='/tmp/story-workbench-plan.png',full_page=True)
                page.locator('#plan-close').click()
                page.locator('#editor').fill(page.locator('#editor').input_value()+'\nUn cambio después de revisar.')
                page.locator('#save').click()
                page.wait_for_function("() => document.querySelector('#book-progress').textContent.includes('0 de 2')")
                page.locator('#template-open').click();page.locator('#template-name').fill('Mara ficticia')
                page.get_by_role('button',name='Crear ficha',exact=True).click()
                page.wait_for_function("() => document.querySelector('#editor').value.includes('Ficha provisional')")
                ficha=next(d for d in server.store.snapshot(project)['documents'] if d['name']=='Mara ficticia.md')
                assert ficha['selected'] is False and ficha['role']=='plan'
                page.reload();page.wait_for_selector('#plan-open:not([disabled])');page.locator('#plan-open').click()
                assert page.locator('#word-goal').input_value()=='80000'
                assert 'El cuarto de radio' in page.locator('.plan-card strong').first.inner_text()
                page.locator('#plan-filter').select_option('revise')
                assert page.locator('.plan-card').count()==1
                page.locator('[data-draft-scene]').click()
                assert page.locator('#mode').input_value()=='draft'
                assert 'Inés escucha una voz imposible' in page.locator('#prompt').input_value()
                assert server.store.load(project)['runs']==[] # Preparar no envía nada.
                # Cambio de proyecto: ni fuentes ni decisiones del anterior.
                page.locator('#new-project').click();page.locator('#project-name').fill('Otro universo')
                page.locator('#wizard-next').click();page.get_by_role('radio',name='Escribir por mi cuenta').check();page.locator('#wizard-create').click()
                page.wait_for_function("() => document.querySelector('#project-title').textContent==='Otro universo'")
                assert 'La última luz' not in page.locator('#documents').inner_text()
                assert 'Conservar incierto' not in page.locator('#decisions').inner_text()
                assert page.locator('#editor').is_enabled()
                assert len(server.store.list_projects())==2
                # El wizard se puede cancelar sin crear nada.
                page.locator('#new-project').click();page.locator('#project-name').fill('Cancelado')
                page.locator('#wizard-next').click();page.locator('#wizard-back').click()
                assert page.locator('#project-name').input_value()=='Cancelado'
                page.locator('#wizard-cancel').click()
                assert len(server.store.list_projects())==2
                # Doble de prueba explícito: la integración real se verifica en live_mvp.py.
                async def fake_interview(project,run,docs):
                    server.assistant.update(project,run['id'],status='completed',text='La biblioteca encendió sus luces sobre el mar.' if run['mode']=='draft' else 'Pregunta de prueba: ¿qué querés que sienta el lector?')
                with patch.object(server.assistant,'execute',fake_interview):
                    page.locator('#new-project').click();page.locator('#project-name').fill('Proyecto guiado')
                    page.locator('#wizard-next').click()
                    assert page.get_by_role('radio',name='Crear conversando').is_checked()
                    page.get_by_role('radio',name='Crear conversando').check()
                    page.locator('#project-idea').fill('Una biblioteca a bordo de un barco.')
                    page.locator('#wizard-create').click()
                    page.get_by_text('Pregunta de prueba: ¿qué querés que sienta el lector?',exact=True).wait_for()
                    guided=next(p for p in server.store.list_projects() if p['title']=='Proyecto guiado')['id']
                    assert server.store.snapshot(guided)['documents']==[]
                    assert page.locator('#mode').input_value()=='interview'
                    assert page.locator('#skill').is_disabled() and page.locator('#skill').is_checked()
                    assert page.locator('.sources').bounding_box()['x'] < page.locator('.assistant').bounding_box()['x']
                    assert not page.locator('.manuscript').is_visible()
                    page.locator('#material-toggle').click();assert page.locator('.manuscript').is_visible()
                    page.locator('#material-toggle').click()
                    page.reload();page.get_by_text('Pregunta de prueba: ¿qué querés que sienta el lector?',exact=True).wait_for()
                    assert len(server.store.load(guided)['runs'])==1
                    assert page.locator('#workflow').input_value()=='guided'
                    page.locator('#focus').click()
                    assert page.locator('.assistant').is_visible() and not page.locator('.manuscript').is_visible()
                    page.locator('#focus').click()
                    page.locator('#workflow').select_option('writing')
                    page.wait_for_function("() => !document.body.classList.contains('guided')")
                    page.locator('#workflow').select_option('guided')
                    page.wait_for_function("() => document.body.classList.contains('guided')")
                    assert len(server.store.load(guided)['runs'])==1
                    page.locator('#prompt').fill('Quiero asombro y esperanza.')
                    page.locator('#send').click()
                    page.wait_for_function("() => document.querySelectorAll('.run').length===2")
                    assert server.store.load(guided)['runs'][-1]['mode']=='interview'
                    assert server.store.load(guided)['runs'][-1]['prompt']=='Quiero asombro y esperanza.'
                    page.locator('#mode').select_option('draft');page.locator('#prompt').fill('Redactá una apertura breve.')
                    page.locator('#send').click()
                    page.get_by_role('button',name='Guardar como borrador provisional').wait_for()
                    assert server.store.snapshot(guided)['documents']==[]
                    page.get_by_role('button',name='Guardar como borrador provisional').click()
                    page.wait_for_function("() => document.querySelector('#editor').value.includes('La biblioteca encendió')")
                    assert len(server.store.snapshot(guided)['documents'])==1
                    page.get_by_role('button',name='Abrir borrador guardado',exact=True).click()
                    assert len(server.store.snapshot(guided)['documents'])==1

                # Progress and collapse survive polling, and new output can be acknowledged.
                assert page.locator('#task-progress progress').get_attribute('value')=='4'
                output=page.locator('.run-output').first
                output.locator(':scope > summary').click()
                assert not output.evaluate('(e)=>e.open')
                page.wait_for_timeout(1800)
                assert not output.evaluate('(e)=>e.open')
                page.reload();page.wait_for_selector('.run-output')
                assert not page.locator('.run-output').first.evaluate('(e)=>e.open')
                page.locator('.run-output').last.get_by_role('button',name='Marcar como visto').click()
                assert 'is-new' not in page.locator('.run-output').last.get_attribute('class')
                # Failed and interrupted jobs never claim full completion.
                with server.store.lock:
                    data=server.store.load(guided);data['runs'][-1].update(status='failed',stage='generation')
                    server.store.persist(data)
                page.wait_for_function("() => document.querySelector('#task-progress progress').value===2")
                assert 'No completado' in page.locator('#task-progress').inner_text()
                # Native CSS 3D, dimensions, safe images, persistence and project isolation.
                page.locator('#book-open').click()
                page.locator('#book-width').fill('140')
                page.locator('#book-height').fill('210')
                page.locator('#book-thickness').fill('32')
                page.locator('#book-name').fill('La biblioteca del mar')
                page.locator('#book-author').fill('Autora ficticia')
                page.get_by_role('button',name='Contraportada',exact=True).click()
                assert page.locator('#book-rotation').input_value()=='-208'
                png=page.locator('.brand-mark').screenshot()
                page.locator('#book-front-file').set_input_files({'name':'cover.png','mimeType':'image/png','buffer':png})
                page.wait_for_function("() => document.querySelector('#book-front').style.backgroundImage.includes('data:image/jpeg')")
                page.locator('#book-save').click()
                page.get_by_text('Maqueta guardada en este proyecto.',exact=True).wait_for()
                page.screenshot(path='/tmp/story-workbench-book-3d.png',full_page=True)
                page.locator('#book-close').click()
                page.reload();page.wait_for_selector('#book-open:not([disabled])');page.locator('#book-open').click()
                assert page.locator('#book-width').input_value()=='140'
                assert page.locator('#book-thickness').input_value()=='32'
                assert 'data:image/jpeg' in page.locator('#book-front').evaluate('(e)=>e.style.backgroundImage')
                assert len(server.store.snapshot(guided)['documents'])==1
                page.set_viewport_size({'width':390,'height':844})
                assert page.locator('#book-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
                page.locator('#book-close').click()
                page.screenshot(path='/tmp/story-workbench-guided-test.png',full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                theme.select_option('light')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.evaluate("localStorage.setItem('sw-theme','invalid')")
                page.reload()
                assert theme.input_value()=='system'
                assert errors==[],errors
                browser.close()
                print('OK navegador: wizard, entrevista simulada sin fuentes, inicio único, chat central, cambio de modo, temas sistema/claro/oscuro, cambios del sistema, persistencia, edición, historial, conflicto, propuesta, decisión, importación segura, foco, exportación, recarga y aislamiento de proyectos.')
        finally:
            server.shutdown();server.server_close()


if __name__=='__main__':main()
