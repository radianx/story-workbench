"""Comprobación del backend incluido usando el Python Windows del paquete (también bajo Wine)."""
import base64
import os
import sys
import tempfile
sys.path.insert(0, sys.argv[1])
from app import AppServer

with tempfile.TemporaryDirectory(prefix='sw-win-') as directory:
    server=AppServer(0,directory)
    try:
        project=server.store.create('Ficción Windows',demo=True)
        doc=server.store.document(project,project['documents'][0]['id'])
        saved=server.store.save_document(project,doc['id'],'Texto aprobado',doc['hash'])
        assert saved['content']=='Texto aprobado' and len(saved['history'])==1
        try:
            AppServer(0,directory)
        except BlockingIOError:
            pass
        else:
            raise AssertionError('Falta bloqueo de instancia')
        if os.environ.get('STORY_VOICE_DIR'):
            assert server.speech.status()['dictation']
            assert server.speech.transcribe(base64.b64encode(b'\0\0'*8000).decode())['text']==''
            print('OK Vosk Windows: biblioteca nativa y modelo español cargados; PCM de silencio reconocido.')
    finally:
        server.server_close()
print('OK runtime Python Windows: servidor, copias ficticias, guardado atómico, historial y lock de instancia.')
