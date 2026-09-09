"""Selección editorial por proyecto, claves separadas y tareas con respuestas simuladas."""
from pathlib import Path
import sys,tempfile,threading
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import AppServer
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory(prefix='sw-engines-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out');project=server.store.create('Ficción de motores',True)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page();page.add_init_script("localStorage.setItem('sw-setup-seen','1')");errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            for provider in ['openai','gemini','anthropic','deepseek','kimi','local']:
                page.locator('#settings-open').click();page.locator('#engine-open').click();page.locator('#engine-provider').select_option(provider);page.locator('#engine-model').fill('ficticio-modelo')
                if provider!='local':page.locator('#engine-key').fill('ficticia-clave-del-test')
                assert page.locator('#engine-remember').is_disabled()
                page.locator('#engine-consent').check();page.locator('#engine-save').click();page.locator('#engine-dialog').wait_for(state='hidden')
                assert server.store.load(project['id'])['engine']['provider']==provider
                assert not page.locator('#ai-options').is_visible()
                page.locator('#settings-close').click()
                with patch.object(server.assistant.providers,'stream',return_value=iter([('Respuesta ficticia de '+provider,'version-ficticia')])):
                    page.locator('#mode').select_option('chat');page.locator('#prompt').fill('Petición '+provider);page.locator('#send').click();page.wait_for_function("()=>state.runs.at(-1)?.status==='completed'&&state.runs.at(-1)?.provider===\""+provider+"\"")
                assert not page.locator('#account-dialog').is_visible()
                assert page.locator('.run-label').last.inner_text().find('experimental')>=0
            page.reload();page.locator('#workspace').wait_for();assert 'experimental' in page.locator('#connection').inner_text()
            page.locator('#settings-open').click();page.locator('#engine-open').click();page.locator('#engine-dialog').wait_for();assert page.locator('#engine-provider').input_value()=='local'
            page.locator('#engine-provider').select_option('kimi');page.locator('#engine-forget').click();page.wait_for_function("()=>document.querySelector('#engine-key-status').textContent==='Sin clave configurada.'")
            assert not server.assistant.providers.status()['kimi'] and not server.realtime.status()['providers']['gemini']
            page.locator('#engine-provider').select_option('codex');page.locator('#engine-save').click();page.locator('#engine-dialog').wait_for(state='hidden');assert page.locator('#ai-options').is_visible()
            assert server.store.load(project['id'])['engine']=={'provider':'codex'}
            page.locator('#settings-close').click()
            assert not errors,errors
            assert all('ficticia-clave' not in file.read_text(errors='ignore') for file in Path(directory).rglob('*.json'))
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK motores UI: seis adaptadores por proyecto, consentimiento, claves aisladas de voz/proyectos, modelo reportado, tareas sin login Codex y vuelta a Codex.')
