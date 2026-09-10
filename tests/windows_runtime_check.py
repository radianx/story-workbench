"""Comprobación del backend incluido usando el Python Windows del paquete (también bajo Wine)."""
import base64
import io
import os
import sys
import tempfile
sys.path.insert(0, sys.argv[1])
from src.app import AppServer

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
        from src.workbench_export import export_book
        from src.workbench_import import import_file
        from PIL import Image
        snapshot=server.store.snapshot(project['id'])
        pdf,mime=export_book(snapshot,'book.pdf')
        assert pdf.startswith(b'%PDF-') and mime=='application/pdf'
        docx,_=export_book(snapshot,'book.docx')
        assert import_file('Ficcion.docx',base64.b64encode(docx).decode())['documents']
        output=io.BytesIO();Image.new('RGB',(8,12),'purple').save(output,format='PNG')
        assert output.getvalue().startswith(b'\x89PNG')
        print('OK formatos Windows: PDF y fuentes, DOCX y Pillow nativo.')
        if os.environ.get('STORY_VOICE_DIR'):
            assert server.speech.status()['dictation']
            assert server.speech.transcribe(base64.b64encode(b'\0\0'*8000).decode())['text']==''
            print('OK Vosk Windows: biblioteca nativa y modelo español cargados; PCM de silencio reconocido.')
    finally:
        server.server_close()
print('OK runtime Python Windows: servidor, copias ficticias, guardado atómico, historial y lock de instancia.')
