"""Una generación optativa en vuelo; resultados provisionales hasta aprobación."""
import base64
import io
import json
import re
import threading
import urllib.error
import urllib.request
from src.workbench_store import check, text_value, uid, Problem
from src.workbench_providers import NoRedirects

MODELS = {'openai': 'gpt-image-2.5-flare', 'gemini': 'gemini-3.1-flash-image'}


class Images:
    def __init__(self, keys):
        self.keys = keys
        self.lock = threading.RLock()
        self.job = None

    def status(self):
        return {name: bool(self.keys(name)) for name in MODELS}

    def start(self, project, body):
        provider = body.get('provider')
        check(provider in MODELS, 'Proveedor de imágenes inválido.')
        check(body.get('consent') is True, 'Confirmá el envío del prompt y el posible coste API.')
        prompt = text_value(body.get('prompt'), 6000, False)
        model = body.get('model') or MODELS[provider]
        check(isinstance(model, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}', model), 'Modelo inválido.')
        key = self.keys(provider)
        check(key, 'Configurá una clave del proveedor de imágenes.')
        shape = body.get('shape', 'portrait')
        check(shape in ('portrait', 'square', 'landscape'), 'Formato de imagen inválido.')
        with self.lock:
            check(not self.job or self.job['status'] not in ('generating', 'cancelling'), 'Ya hay una imagen en generación.', 409)
            job = dict(id=uid(), project=project, provider=provider, model=model, prompt=prompt, shape=shape, status='generating')
            self.job = job
            threading.Thread(target=self.generate, args=(job, key), daemon=True).start()
            return self.snapshot(job['id'], project)

    def snapshot(self, id, project):
        with self.lock:
            check(self.job and self.job['id'] == id and self.job['project'] == project, 'Generación no encontrada.', 404)
            return dict(self.job)

    def cancel(self, id, project):
        with self.lock:
            self.snapshot(id, project)
            self.job['status'] = 'cancelling' if self.job['status'] == 'generating' else 'cancelled'
            self.job.pop('data', None)
            return dict(status=self.job['status'])

    def generate(self, job, key):
        try:
            if job['provider'] == 'openai':
                url = 'https://api.openai.com/v1/images/generations'
                payload = dict(model=job['model'], prompt=job['prompt'], n=1, output_format='png', quality='medium',
                               size={'portrait':'1024x1536','square':'1024x1024','landscape':'1536x1024'}[job['shape']])
                headers = {'Authorization': 'Bearer ' + key}
            else:
                url = 'https://generativelanguage.googleapis.com/v1/models/' + job['model'] + ':generateContent'
                payload = dict(contents=[dict(parts=[dict(text=job['prompt'])])], generationConfig=dict(responseModalities=['IMAGE'],
                               imageConfig=dict(aspectRatio={'portrait':'2:3','square':'1:1','landscape':'3:2'}[job['shape']])))
                headers = {'x-goog-api-key': key}
            request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={**headers, 'Content-Type':'application/json'})
            with urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirects()).open(request, timeout=180) as response:
                raw = response.read(32_000_001)
            check(len(raw) <= 32_000_000, 'La respuesta de imagen supera el límite.')
            result = json.loads(raw)
            if job['provider'] == 'openai':
                encoded = result.get('data', [{}])[0].get('b64_json', '')
            else:
                encoded = next((part.get('inlineData', {}).get('data') for candidate in result.get('candidates', [])
                                for part in candidate.get('content', {}).get('parts', []) if part.get('inlineData', {}).get('data')), '')
            check(isinstance(encoded, str) and encoded, 'El proveedor no devolvió una imagen. Puede haber rechazado la petición.')
            data = base64.b64decode(encoded, validate=True)
            check(len(data) <= 15_000_000, 'Imagen demasiado grande.')
            from PIL import Image
            with Image.open(io.BytesIO(data)) as image:
                check(image.format in ('PNG', 'JPEG') and image.width * image.height <= 20_000_000, 'Formato o tamaño de imagen no compatible.')
                width, height, format = image.width, image.height, image.format
                image.verify()
            with self.lock:
                if job['status'] != 'generating':
                    job['status'] = 'cancelled'
                    return
                job.update(status='ready', data=encoded, mime='image/png' if format == 'PNG' else 'image/jpeg', width=width, height=height)
        except Exception as error:
            with self.lock:
                if job['status'] == 'cancelling':
                    job['status'] = 'cancelled'
                else:
                    message = str(error) if isinstance(error, Problem) else ('El proveedor rechazó la solicitud; revisá clave, modelo y cuota.' if isinstance(error, urllib.error.HTTPError) else 'No se pudo generar la imagen. Revisá la conexión y el proveedor.')
                    job.update(status='failed', error=message)

    def save(self, store, project, id):
        from src.workbench_store import atomic
        with self.lock, store.lock:
            job = self.snapshot(id, project)
            data = store.load(project)
            existing = next((image for image in data.get('images', []) if image['id'] == id), None)
            if existing:
                return existing
            check(job['status'] == 'ready', 'La imagen todavía no está lista.')
            check(len(data.get('images', [])) < 30, 'Máximo de 30 imágenes por proyecto.')
            folder = store.path(project, 'images')
            folder.mkdir(exist_ok=True)
            file = id + ('.png' if job['mime'] == 'image/png' else '.jpg')
            path = store.path(project, 'images', file)
            record = {key: job[key] for key in ('id', 'provider', 'model', 'prompt', 'mime', 'width', 'height')}
            record['file'] = file
            atomic(path, base64.b64decode(job['data'], validate=True))
            data.setdefault('images', []).append(record)
            try:
                store.persist(data)
            except Exception:
                if not any(item['id'] == id for item in store.load(project).get('images', [])):
                    path.unlink(missing_ok=True)
                raise
            return record
