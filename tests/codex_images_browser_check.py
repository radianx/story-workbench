"""Clickable Codex attachments through HTTP, current chat, history and gallery."""
from pathlib import Path
import asyncio
import sys
import tempfile
import threading
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.app import AppServer
from test_codex_images import ImageServer
from test_images import png
from playwright.sync_api import sync_playwright

with tempfile.TemporaryDirectory(prefix='sw-attachments-') as directory:
    server = AppServer(0, directory); server.account.set(status='signed_out')
    data = server.store.create('Ficción visual', workflow='writing'); project = data['id']
    with patch('threading.Thread.start'):
        server.assistant.start(project, 'chat', 'Generá un faro.', False)
    with patch('src.workbench_ai.Server', ImageServer), patch('src.workbench_ai.shutil.which', return_value='/usr/bin/true'):
        asyncio.run(server.assistant.execute(project, server.store.load(project)['runs'][-1], []))
    server.assistant.active = None
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1440, 'height':1000})
            errors=[]; page.on('pageerror', lambda error: errors.append(str(error)))
            page.add_init_script("localStorage.setItem('sw-setup-seen','1'); localStorage.setItem('sw-theme','dark')")
            page.goto(server.origin+'/#token='+server.token)
            page.wait_for_function('() => document.querySelector("#runs .image-attachment img")?.naturalWidth === 8')
            card = page.locator('#runs .image-attachment')
            card.wait_for(state='visible')
            card.press('Enter')
            page.wait_for_function('() => document.querySelector("#image-viewer-original").naturalWidth === 8')
            before = page.locator('#image-viewer-original').bounding_box()['width']
            page.locator('#image-zoom').fill('200'); page.locator('#image-zoom').dispatch_event('input')
            assert page.locator('#image-viewer-original').bounding_box()['width'] == before * 2
            with page.expect_download() as result:
                page.locator('#image-viewer-download').click()
            assert Path(result.value.path()).read_bytes() == png()
            page.keyboard.press('Escape'); assert not page.locator('#image-viewer').is_visible()
            assert card.evaluate('(el)=>el===document.activeElement')
            page.reload()
            page.wait_for_function('() => document.querySelector("#runs .image-attachment img")?.naturalWidth === 8')
            page.locator('#images-open').click()
            page.wait_for_function('() => document.querySelector("#image-gallery .image-attachment img")?.naturalWidth === 8')
            page.locator('#image-gallery .image-attachment').click()
            page.locator('#image-viewer').wait_for(state='visible')
            page.keyboard.press('Escape'); page.locator('#images-close').click()
            # Archive chat through the same persisted operation as the UI.
            server.store.reset_conversation(server.store.load(project))
            page.reload(); page.wait_for_function('() => state?.conversations?.length === 1')
            assert page.locator('#runs .image-attachment').count() == 0
            page.locator('#previous-chats summary').click()
            page.locator('#chat-links button').click()
            page.wait_for_function('() => document.querySelector("#chat-history .image-attachment img")?.naturalWidth === 8')
            page.locator('#chat-history .image-attachment').click()
            page.locator('#image-viewer').wait_for(state='visible')
            page.keyboard.press('Escape'); page.locator('#chat-history-close').click()
            # Image endpoint remains authenticated and scoped by project.
            image = server.store.load(project)['images'][0]
            endpoint = f'/api/projects/{project}/images/{image["id"]}'
            assert page.request.get(server.origin+endpoint).status == 401
            other = server.store.create('Otro proyecto')['id']
            assert page.request.get(server.origin+endpoint.replace(project, other), headers={'Authorization':'Bearer '+server.token}).status == 404
            assert not errors, errors
            browser.close()
        print('OK Codex attachments: thumbnail, keyboard viewer/zoom, original download, reload, gallery, archived chat, auth and project isolation.')
    finally:
        server.shutdown(); server.server_close()
