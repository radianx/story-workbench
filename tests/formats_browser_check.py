"""EPUB/DOCX, PDF and image approval through the actual UI, with a fake image provider."""
from pathlib import Path
import sys
import base64
import tempfile
import threading
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.app import AppServer
from src.workbench_export import export_book
from src.workbench_images import Images
from test_formats import epub
from test_images import png
from playwright.sync_api import sync_playwright


def generate(self,job,key):
    with self.lock:
        job.update(status='ready',data=base64.b64encode(png()).decode(),mime='image/png',width=8,height=12)

with tempfile.TemporaryDirectory(prefix='sw-formats-') as directory, patch.object(Images,'generate',generate):
    server=AppServer(0,directory)
    server.account.set(status='signed_out')
    data=server.store.create('Formatos ficticios');project=data['id']
    server.assistant.providers.configure('gemini','test-key-only')
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000})
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token)
            page.wait_for_function('() => state?.id')
            # Static controls are already in place before settings initialization.
            assert page.locator('.composer-entry #send').count()==1
            assert page.locator('#settings-general #app-font').count()==1
            page.locator('#files').set_input_files({'name':'Ficción.epub','mimeType':'application/epub+zip','buffer':epub()})
            page.wait_for_function('() => state.documents.some(d=>d.content.includes("Primero"))')
            source,_=export_book({'title':'DOCX','documents':[{'role':'manuscrito','content':'Texto DOCX importado.'}]},'book.docx')
            page.locator('#files').set_input_files({'name':'Ficción.docx','mimeType':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','buffer':source})
            page.wait_for_function('() => state.documents.some(d=>d.content.includes("Texto DOCX importado"))')
            assert not any(d['selected'] for d in server.store.load(project)['documents'][1:])
            page.locator('#plan-open').click()
            with page.expect_download() as download:
                page.locator('#book-pdf').click()
            assert Path(download.value.path()).read_bytes().startswith(b'%PDF-')
            page.locator('#plan-close').click()
            page.locator('#settings-open').click()
            page.locator('#image-settings-provider').select_option('gemini')
            page.locator('#image-key').fill('test-image-provider')
            page.locator('#image-key-save').click()
            page.get_by_text('Clave preparada. El motor editorial del proyecto conserva su selección.',exact=True).wait_for()
            assert not server.store.load(project).get('engine')
            page.locator('#settings-close').click()
            page.locator('#images-open').click()
            page.locator('#images-dialog').wait_for(state='visible')
            assert page.locator('#image-provider').input_value()=='gemini'
            page.locator('#image-prompt').fill('Un faro violeta junto al mar.');page.locator('#image-consent').check()
            page.locator('#image-generate').click();page.locator('#image-preview').wait_for(state='visible')
            assert page.locator('#image-preview').evaluate('(img)=>img.complete && img.naturalWidth===8')
            assert not server.store.load(project).get('images')
            page.locator('#image-save').click()
            page.locator('#image-gallery article').wait_for()
            assert len(server.store.load(project)['images'])==1
            with page.expect_download() as download:
                page.locator('#image-gallery').get_by_text('Descargar imagen',exact=True).click()
            assert Path(download.value.path()).read_bytes()==png()
            page.locator('#image-gallery').get_by_text('Usar como portada 3D').click()
            page.locator('#book-dialog').wait_for(state='visible')
            page.wait_for_function('() => book.front.startsWith("data:image/jpeg")')
            assert not server.store.load(project).get('production')
            page.locator('#book-save').click()
            page.wait_for_function('() => !bookDirty')
            assert server.store.load(project)['production']['front'].startswith('data:image/jpeg')
            page.locator('#book-close').click()
            page.reload();page.wait_for_function('() => state?.id')
            page.locator('#images-open').click();page.locator('#image-gallery article').wait_for()
            assert page.locator('#image-key').input_value()==''
            assert not errors,errors
            browser.close()
        print('OK formats UI: EPUB/DOCX copies, PDF download, image preview/approval/download/cover/persistence. No paid calls.')
    finally:server.shutdown();server.server_close()
