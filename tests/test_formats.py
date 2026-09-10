import base64
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from src.workbench_store import Store, Problem
from src.workbench_import import import_file, MAX_TEXT, xml, W
from src.workbench_export import export_book
from src.workbench_migrations import migrate_project


def archive(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, text in entries.items(): z.writestr(name, text)
    return out.getvalue()


def epub():
    return archive({'META-INF/container.xml':'<container><rootfiles><rootfile full-path="OPS/book.opf"/></rootfiles></container>',
        'OPS/book.opf':'<package><manifest><item id="a" href="a.xhtml" media-type="application/xhtml+xml"/><item id="b" href="b.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>',
        'OPS/a.xhtml':'<html><body><h1>Segundo</h1><p>La niña volvió.</p></body></html>',
        'OPS/b.xhtml':'<html><head><title>No copiar</title></head><body><h1>Primero</h1><p>El río &amp; su voz.</p><script>malicioso()</script><img src="https://example.invalid/tracker"/></body></html>'})


class Formats(unittest.TestCase):
    def test_epub_reading_order_and_text_only(self):
        source = epub()
        result = import_file('Ficción.epub', base64.b64encode(source).decode())
        self.assertEqual(len(result['documents']),2)
        self.assertIn('Primero',result['documents'][0]['content'])
        self.assertIn('río & su voz.',result['documents'][0]['content'])
        self.assertNotIn('malicioso',str(result))
        self.assertNotIn('No copiar',str(result))
        self.assertEqual(source,epub())

    def test_docx_roundtrip_and_multibyte_split(self):
        source, _ = export_book({'title':'Ficción','documents':[{'role':'manuscrito','content':'# Capítulo\n\nLa niña & el río.\nSegunda línea.'}]},'book.docx')
        docs = import_file('Ficción.docx',base64.b64encode(source).decode())['documents']
        self.assertIn('# Capítulo',docs[0]['content'])
        self.assertIn('niña & el río.\nSegunda línea.',docs[0]['content'])
        text = 'á'*(MAX_TEXT+1)
        parts = import_file('ñ'*80+'.txt',base64.b64encode(text.encode()).decode())['documents']
        self.assertEqual(''.join(d['content'] for d in parts),text)
        self.assertTrue(all(len(d['name'].encode())<=200 and len(d['content'].encode())<=MAX_TEXT for d in parts))

    def test_docx_tables_notes_and_deleted_text(self):
        source=archive({'word/document.xml':f'<w:document xmlns:w="{W[1:-1]}"><w:body><w:p><w:r><w:t>Actual</w:t></w:r><w:del><w:r><w:delText>Descartado</w:delText></w:r></w:del><w:r><w:footnoteReference w:id="1"/></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Primero</w:t></w:r></w:p><w:p><w:r><w:t>Segundo</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>',
            'word/footnotes.xml':f'<w:footnotes xmlns:w="{W[1:-1]}"><w:footnote w:id="1"><w:p><w:r><w:t>Una nota.</w:t></w:r></w:p></w:footnote></w:footnotes>'})
        result=import_file('Tabla.docx',base64.b64encode(source).decode())['documents'][0]['content']
        self.assertIn('Primero Segundo',result);self.assertIn('[nota 1] Una nota.',result)
        self.assertNotIn('Descartado',result)

    def test_untrusted_containers(self):
        for entries in [{'../escape':'bad'}, {'word/document.xml':'<!DOCTYPE x [<!ENTITY a "bad">]><x>&a;</x>'}]:
            with self.assertRaises((ValueError,Problem)):
                import_file('bad.docx',base64.b64encode(archive(entries)).decode())
        with self.assertRaises(Problem): xml('<!DOCTYPE x><x/>'.encode('utf-16'))
        with self.assertRaises((ValueError,Problem)): import_file('bad.epub','!!!')
        with self.assertRaises(Problem): import_file('bad.exe',base64.b64encode(b'text').decode())

    def test_migrations_preserve_legacy_and_reject_future(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory); data=store.create('Migración',True)
            path=store.path(data['id'],'project.json'); original=json.loads(path.read_text())
            for key in ('schema_version','workflow','purpose','conversations'):original.pop(key,None)
            original['custom_metadata']={'kept':True}
            path.write_text(json.dumps(original)); before=path.read_bytes()
            migrated=store.load(data['id'])
            self.assertEqual(migrated['schema_version'],1)
            self.assertEqual(migrated,migrate_project(migrated))
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(migrated['documents'],original['documents'])
            store.persist(migrated); self.assertTrue(store.load(data['id'])['custom_metadata']['kept'])
            migrated['schema_version']=999
            with self.assertRaises(Problem):store.persist(migrated)
            self.assertEqual(store.load(data['id'])['schema_version'],1)

    def test_bulk_import_atomic_and_unselected(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);data=store.create('Importación');before=store.snapshot(data['id'])
            docs=[dict(name='A',content='Ficción',role='manuscrito'),dict(name='B',content='Otra',role='manuscrito')]
            with patch.object(store,'persist',side_effect=OSError('disco')):
                with self.assertRaises(OSError):store.add_documents(data,docs)
            self.assertEqual(store.snapshot(data['id']),before)
            self.assertEqual(len(list(store.path(data['id'],'documents').glob('*'))),len(before['documents']))
            store.add_documents(data,docs)
            added=store.snapshot(data['id'])['documents'][-2:]
            self.assertEqual([d['content'] for d in added],['Ficción','Otra'])
            self.assertFalse(any(d['selected'] for d in added))

    def test_import_preserves_files_after_commit_error(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory);data=store.create('Copia recuperable')
            persist=store.persist
            def committed_then_failed(value):
                persist(value)
                raise OSError('Error al sincronizar después de guardar')
            with patch.object(store,'persist',side_effect=committed_then_failed):
                with self.assertRaises(OSError):store.add_documents(data,[dict(name='Copia',role='manuscrito',content='Texto conservado.')])
            self.assertEqual(store.snapshot(data['id'])['documents'][-1]['content'],'Texto conservado.')

    def test_pdf_real_pages_size_and_text(self):
        data={'title':'Ficción del río','production':{'width':152.4,'height':228.6},'documents':[{'role':'manuscrito','content':'# Primer capítulo\n\n'+('La niña escuchó el río.\n\n'*160)},{'role':'manuscrito','content':'# Final\n\nDespués volvió.'}]}
        output,mime=export_book(data,'book.pdf');self.assertEqual(mime,'application/pdf');self.assertTrue(output.startswith(b'%PDF-'))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'book.pdf';path.write_bytes(output)
            text=subprocess.check_output(['pdftotext',str(path),'-']).decode()
            self.assertIn('Ficción del río',text);self.assertIn('Después volvió.',text)
            self.assertEqual(text.count('La niña escuchó el río.'),160)
            self.assertGreater(text.count('\f'),3)
            info=subprocess.check_output(['pdfinfo',str(path)]).decode()
            self.assertIn('432 x 648 pts',info)
        data['title']='漢字'
        with self.assertRaises(Problem):export_book(data,'book.pdf')
