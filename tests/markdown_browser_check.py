"""Markdown real en chat, historial y editor; ficción temporal y ninguna llamada IA."""
import sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.app import AppServer
from playwright.sync_api import sync_playwright

TEXT='''# Un título

**Negrita**, *cursiva*, ~~tachado~~ y `**código literal**`.

> Una cita con **énfasis**.

1. Primero
   - Anidado
2. Segundo

---

| Personaje | Decisión | Consecuencia | Momento |
| :--- | :---: | ---: | --- |
| **Inés** | Volver | Duda | Mañana |

```python
print("<script>literal</script>")
```

[Referencia](https://example.org/historia)

<img src="https://example.org/tracker" onerror="window.injected=true">
<script>window.injected=true</script>
[No ejecutar](javascript:alert(1))
[No archivo](file:///tmp/privado)
![Imagen sin descargar](https://example.org/image.png)
'''
with tempfile.TemporaryDirectory(prefix='sw-markdown-') as directory:
    server=AppServer(0,directory);server.account.set(status='signed_out')
    project=server.store.create('Formatos ficticios',True)['id']
    with server.store.lock:
        data=server.store.load(project)
        data['runs']=[dict(id='format-run',mode='chat',status='running',prompt='Mostrar formatos',text='**Parcial',sources=[],date=0)]
        server.store.persist(data)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport=dict(width=1440,height=1000));errors=[];external=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:external.append(r.url) if not r.url.startswith(server.origin+'/') else None)
            page.add_init_script("localStorage.setItem('sw-setup-seen','1')")
            page.goto(server.origin+'/#token='+server.token)
            page.locator('.run-text').wait_for()
            assert '**Parcial' in page.locator('.run-text').inner_text()
            with server.store.lock:
                data=server.store.load(project);data['runs'][0].update(text=TEXT,status='completed',team=dict(model='ficticio',effort='low'),team_workers=[dict(title='Lector',assignment='Opinar',status='completed',text='**Aporte**')])
                server.store.persist(data)
            output=page.locator('#runs .run-output > .run-text')
            output.locator('table').wait_for()
            for selector in ['h1','strong','em','s','blockquote strong','ol ul li','hr','pre code','table tbody strong']:
                assert output.locator(selector).count(),selector
            assert output.locator('code').first.inner_text()=='**código literal**'
            assert output.locator('td').nth(2).evaluate('(e)=>getComputedStyle(e).textAlign')=='right'
            assert output.locator('a[href="https://example.org/historia"]').count()==1
            for link in output.locator('a').all():
                assert link.get_attribute('href').startswith('https://example.org/') and link.get_attribute('rel')=='noopener noreferrer'
            assert not output.locator('script,img,iframe,style,[style],[onclick],[onerror]').count()
            assert not page.evaluate('window.injected')
            assert page.locator('.team-results strong').text_content()=='Aporte'
            page.locator('#editor').fill(TEXT);page.locator('#save').click()
            page.wait_for_function("() => !dirty");page.locator('[data-view=preview]').click()
            assert page.locator('#preview table').count()==1
            assert '<script>window.injected=true</script>' in page.locator('#preview').inner_text()
            # Tablas accesibles y contenidas incluso en una ventana compacta.
            page.set_viewport_size(dict(width=390,height=844))
            table=output.locator('.markdown-table');table.scroll_into_view_if_needed();table.focus()
            assert table.evaluate('(e)=>e.scrollWidth>e.clientWidth')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path='/tmp/sw-markdown-compact.png',full_page=True)
            page.set_viewport_size(dict(width=1440,height=1000))
            page.evaluate('window.scrollTo(0,0)')
            page.on('dialog',lambda d:d.accept())
            page.locator('#new-thread').click();page.locator('#previous-chats summary').click()
            page.locator('[data-chat]').first.click()
            assert page.locator('#chat-history-content table').count()==1
            assert page.locator('#chat-history-content .team-results strong').text_content()=='Aporte'
            assert server.store.snapshot(project)['runs'][0]['text']==TEXT
            assert not errors and not external,(errors,external)
            browser.close()
    finally:server.shutdown();server.server_close()
print('OK Markdown: streaming, formatos, tablas, historial/equipo, vista previa y seguridad; sin IA ni recursos externos.')
