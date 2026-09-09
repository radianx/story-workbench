"""Comprobación del backend incluido usando el Python Windows del paquete (también bajo Wine)."""
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
    finally:
        server.server_close()
print('OK runtime Python Windows: servidor, copias ficticias, guardado atómico, historial y lock de instancia.')
