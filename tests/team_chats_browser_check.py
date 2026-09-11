"""Equipo acotado y chats archivados con servidores IA simulados, sin cuota real."""
import sys,tempfile,threading,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.app import AppServer
from test_team import FakeServer
from test_desktop_features import MODELS
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory(prefix='sw-team-chats-') as directory:
    server=AppServer(0,directory);server.account.set(status='connected',models=MODELS)
    project=server.store.create('Lectores de prueba',True)['id']
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with patch.dict(os.environ, {'STORY_CODEX_BINARY': sys.executable}),sync_playwright() as p,patch('src.workbench_ai.Server',FakeServer),patch('src.workbench_team.Server',FakeServer):
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token);page.locator('#workspace').wait_for()
            assert page.locator('#team-configure').is_hidden()
            page.locator('#mode').select_option('panel');page.locator('#team-enabled').check()
            assert page.locator('#team-settings').is_visible()
            assert not page.locator('#settings-dialog').is_visible()
            page.locator('#team-model').select_option('modelo-b')
            page.locator('#team-model-1').select_option('modelo-a')
            page.locator('#team-effort-1').select_option('medium')
            page.locator('#team-save').click();page.wait_for_function("()=>state.team_preferences?.model==='modelo-b'")
            assert page.locator('#team-settings').is_hidden()
            assert page.evaluate("state.team_preferences.workers[1]")=={'model':'modelo-a','effort':'medium'}
            page.locator('#team-configure').click();page.locator('#team-close').click()
            page.locator('#mode').select_option('interview')
            assert not page.locator('#team-enabled').is_visible()
            page.locator('#mode').select_option('panel');page.locator('#team-enabled').check()
            assert 'más cuota' in page.locator('#team-warning').inner_text()
            page.locator('#team-close').click()
            page.locator('#settings-open').click();page.locator('#skill').uncheck();page.locator('#settings-close').click();page.locator('#prompt').fill('Primera lectura ciega');page.locator('#send').click()
            page.wait_for_function("()=>state.runs.at(-1)?.status==='completed'")
            assert page.locator('#runs .team-results').count()==1
            assert page.locator('.run-time').inner_text().startswith('Última respuesta:')
            assert page.locator('.run-time').get_attribute('datetime')
            assert page.locator('.run-label').evaluate('el=>{const a=el.firstElementChild.getBoundingClientRect(),b=el.lastElementChild.getBoundingClientRect();return b.left>=a.right}')
            page.locator('#runs .team-results > summary').click()
            assert '2/2' in page.locator('#runs .team-results > summary').inner_text()
            page.locator('#runs .team-results details > summary').first.click()
            page.evaluate("lastRuns='';renderAssistant()")
            assert page.locator('#runs .team-results').evaluate('e=>e.open')
            assert page.locator('#runs .team-results details').first.evaluate('e=>e.open')
            assert not page.locator('#team-enabled').is_checked()
            old_thread=server.store.load(project)['thread'];turns=FakeServer.count
            page.locator('#prompt').fill('Idea que no envié');page.locator('#new-thread').focus();page.keyboard.press('Enter')
            page.wait_for_function("()=>state.history_start===1")
            assert page.locator('#runs .run').count()==0 and page.locator('#prompt').input_value()==''
            assert not page.locator('#task-progress').is_visible()
            assert not server.store.load(project)['thread']
            page.locator('#previous-chats > summary').click();page.locator('[data-chat]').click()
            assert 'Síntesis para el autor.' in page.locator('#chat-history-content').inner_text()
            assert 'Idea que no envié' in page.locator('#chat-history-content').inner_text()
            page.keyboard.press('Escape');assert not page.locator('#chat-history').is_visible()
            assert FakeServer.count==turns and not server.store.load(project)['thread']
            with server.store.lock:
                data=server.store.load(project);data['workflow']='guided';server.store.persist(data)
            page.reload();page.locator('#workspace').wait_for()
            assert page.locator('#runs .run').count()==0 and FakeServer.count==turns
            assert page.evaluate("state.team_preferences.effort")=='low'
            page.locator('#mode').select_option('diagnosis');page.locator('#settings-open').click();page.locator('#skill').uncheck();page.locator('#settings-close').click();page.locator('#prompt').fill('Mensaje nuevo');page.locator('#send').click()
            page.wait_for_function("()=>state.runs.length===2&&state.runs.at(-1).status==='completed'")
            assert page.locator('#runs .run').count()==1
            assert server.store.load(project)['thread']!=old_thread
            assert 'Primera lectura ciega' not in page.locator('#runs').inner_text()
            assert not server.store.load(project)['runs'][-1].get('team')
            page.set_viewport_size({'width':390,'height':844});page.locator('#team-enabled').check()
            assert page.locator('#team-settings').evaluate('e=>e.scrollWidth<=e.clientWidth')
            page.screenshot(path='/tmp/sw-team-mobile.png')
            assert not errors,errors
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK equipo configurable, panel ciego, opt-in, cuota visible, nueva conversación vacía, archivo consultable, borrador preservado, recarga y contexto nuevo.')
