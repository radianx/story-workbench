"""Adaptadores editoriales experimentales, sin SDK ni fallback entre proveedores."""
import json
import re
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from workbench_store import check, Problem

PROVIDERS = {'openai':'OpenAI API', 'gemini':'Google Gemini', 'anthropic':'Anthropic',
             'deepseek':'DeepSeek', 'kimi':'Kimi', 'local':'Servidor local'}
ENDPOINTS = {'openai':'https://api.openai.com/v1/responses',
             'gemini':'https://generativelanguage.googleapis.com/v1beta/models/',
             'anthropic':'https://api.anthropic.com/v1/messages',
             'deepseek':'https://api.deepseek.com/chat/completions',
             'kimi':'https://api.moonshot.ai/v1/chat/completions'}


def engine_preferences(value):
    check(isinstance(value, dict), 'Motor inválido.')
    provider = value.get('provider', 'codex')
    check(provider == 'codex' or provider in PROVIDERS, 'Proveedor inválido.')
    if provider == 'codex':
        return {'provider':'codex'}
    model = value.get('model', '')
    check(isinstance(model, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}', model),
          'Ingresá el ID del modelo que ofrece tu proveedor.')
    if provider == 'gemini':
        check(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}', model), 'Usá el ID Gemini sin el prefijo models/.')
    result = dict(provider=provider, model=model)
    if provider == 'local':
        endpoint = value.get('endpoint', 'http://127.0.0.1:11434/v1')
        check(isinstance(endpoint, str) and len(endpoint)<200, 'Dirección local inválida.')
        try:
            url = urlsplit(endpoint)
            check(url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost', '::1')
                  and url.port is not None and not url.username and not url.password
                  and url.path.rstrip('/') == '/v1' and not url.query and not url.fragment,
                  'Usá http://127.0.0.1:PUERTO/v1 para el servidor local.')
        except ValueError:
            raise Problem('Dirección local inválida.') from None
        # Evitar resolución DNS y proxies en el destino local.
        result['endpoint'] = f'http://{"[::1]" if url.hostname=="::1" else "127.0.0.1"}:{url.port}/v1'
    return result


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Problem('El proveedor intentó redirigir la petición. No se reenviaron datos ni clave.')


class Providers:
    def __init__(self):
        self.keys = {}

    def status(self):
        return {p: bool(self.keys.get(p)) for p in PROVIDERS}

    def configure(self, provider, key):
        check(provider in PROVIDERS, 'Proveedor inválido.')
        check(isinstance(key, str) and (key == '' or 8 <= len(key) <= 2048)
              and all(32 < ord(c) < 127 for c in key), 'Ingresá una clave API válida o usá Olvidar clave.')
        self.keys[provider] = key
        return self.status()

    def request(self, engine, instructions, text):
        engine = engine_preferences(engine)
        provider, model = engine['provider'], engine['model']
        key = self.keys.get(provider, '')
        check(provider == 'local' or key, 'Configurá la clave del proveedor editorial en Configuración.')
        headers = {'Content-Type':'application/json', 'Accept':'text/event-stream'}
        if key:
            headers['Authorization'] = 'Bearer ' + key
        body = dict(model=model, stream=True)
        endpoint = ENDPOINTS.get(provider)
        if provider == 'openai':
            body.update(instructions=instructions, input=text, store=False, max_output_tokens=8192)
        elif provider == 'gemini':
            headers.pop('Authorization', None);headers['x-goog-api-key'] = key
            endpoint += model + ':streamGenerateContent?alt=sse'
            body = dict(systemInstruction={'parts':[{'text':instructions}]},
                        contents=[{'role':'user','parts':[{'text':text}]}],
                        generationConfig={'maxOutputTokens':8192})
        elif provider == 'anthropic':
            headers.pop('Authorization', None);headers.update({'x-api-key':key, 'anthropic-version':'2023-06-01'})
            body.update(system=instructions, messages=[{'role':'user','content':text}], max_tokens=8192)
        else:
            if provider == 'local':
                endpoint = engine['endpoint'] + '/chat/completions'
            body.update(messages=[{'role':'system','content':instructions},{'role':'user','content':text}], max_tokens=8192)
        return urllib.request.Request(endpoint, data=json.dumps(body, ensure_ascii=False).encode(), headers=headers)

    def stream(self, engine, instructions, text, cancel):
        request = self.request(engine, instructions, text)
        # ponytail: socket con espera máxima de 30 s; cancelar puede esperar ese intervalo sin datos.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirects())
        deadline = time.monotonic()+240
        try:
            with opener.open(request, timeout=30) as response:
                check('text/event-stream' in response.headers.get('Content-Type',''), 'El proveedor no devolvió un flujo SSE compatible.')
                completed, stop, data, total = False, False, [], 0
                while not completed:
                    if cancel.is_set():
                        return
                    check(time.monotonic()<deadline, 'La tarea superó cuatro minutos.')
                    line = response.readline(1_000_001)
                    total += len(line)
                    check(len(line)<=1_000_000 and total<=4_000_000, 'Respuesta del proveedor demasiado grande.')
                    check(line, 'El proveedor cortó la respuesta antes de terminar.')
                    if line.strip():
                        if line.startswith(b'data:'):
                            data.append(line[5:].strip())
                        continue
                    if not data:
                        continue
                    raw = b'\n'.join(data); data = []
                    if raw == b'[DONE]':
                        check(stop, 'El proveedor terminó sin confirmar una respuesta completa.')
                        completed = True
                        continue
                    event = json.loads(raw)
                    check(isinstance(event, dict) and not event.get('error'), 'El proveedor rechazó la tarea. Revisá el modelo, clave y cuota; no se cambió de proveedor.')
                    fragment, final, reason, reported = '', False, None, event.get('model') or event.get('modelVersion')
                    provider = engine['provider']
                    if provider == 'openai':
                        kind = event.get('type')
                        check(kind not in ('error','response.failed','response.incomplete','response.refusal.delta'), 'Respuesta incompleta o rechazada por OpenAI.')
                        if kind == 'response.output_text.delta':
                            fragment = event.get('delta','')
                        if kind == 'response.completed':
                            final = event.get('response',{}).get('status') == 'completed'
                            check(final, 'OpenAI no confirmó la respuesta.')
                            reported = event.get('response',{}).get('model')
                    elif provider == 'anthropic':
                        kind = event.get('type'); check(kind!='error', 'Anthropic rechazó la tarea.')
                        if kind == 'message_start':
                            reported = event.get('message',{}).get('model')
                        if kind == 'content_block_delta' and event.get('delta',{}).get('type')=='text_delta':
                            fragment = event['delta']['text']
                        if kind == 'message_delta':
                            reason = event.get('delta',{}).get('stop_reason')
                        if kind == 'message_stop':
                            check(stop, 'Anthropic no confirmó una respuesta completa.');final=True
                    elif provider == 'gemini':
                        check(not event.get('promptFeedback',{}).get('blockReason'), 'Gemini bloqueó la petición.')
                        candidates = event.get('candidates',[])
                        if candidates:
                            candidate = candidates[0]
                            fragment = ''.join(p.get('text','') for p in candidate.get('content',{}).get('parts',[]) if not p.get('thought'))
                            reason = candidate.get('finishReason');final = reason=='STOP'
                    else:
                        choices = event.get('choices',[])
                        if choices:
                            delta = choices[0].get('delta',{})
                            check(not delta.get('tool_calls') and not delta.get('refusal'), 'El modelo no devolvió texto editorial revisable.')
                            fragment = delta.get('content') or ''
                            reason = choices[0].get('finish_reason')
                    if reason:
                        check(reason in ('stop','end_turn','STOP'), 'Respuesta incompleta, filtrada o limitada. Reducí el alcance y volvé a enviar.')
                        stop = True
                    check(isinstance(fragment,str), 'Texto de respuesta inválido.')
                    if reported:
                        check(isinstance(reported,str) and len(reported)<=160, 'Modelo reportado inválido.')
                    if fragment or reported:
                        yield fragment, reported
                    completed = final
        except urllib.error.HTTPError as error:
            raise Problem(f'El proveedor respondió HTTP {error.code}. Revisá clave, modelo, cuota y compatibilidad. Sin fallback.') from None
        except (OSError, ValueError, KeyError, TypeError):
            raise Problem('No se pudo completar la respuesta del proveedor. Revisá conexión y compatibilidad. Sin fallback.') from None
