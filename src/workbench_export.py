"""Compilación de copias guardadas: Markdown y DOCX básico con biblioteca estándar."""
import io
import json
import re
import zipfile
from xml.sax.saxutils import escape
from src.workbench_store import check


def export_book(data, format):
    docs = [d for d in data['documents'] if d['role'] == 'manuscrito']
    check(docs and any(d['content'].strip() for d in docs), 'Todavía no hay texto de manuscrito para exportar.')
    check(format in ('book.md', 'book.docx', 'book.pdf'), 'Formato inválido.')
    if format == 'book.pdf':
        from src.workbench_pdf import export_pdf
        return export_pdf(data, docs)
    if format == 'book.md':
        text = '# ' + data['title'] + '\n\n' + '\n\n---\n\n'.join(d['content'] for d in docs)
        return text.encode('utf-8'), 'text/markdown; charset=utf-8'

    def paragraph(text, heading=0, page=False):
        # XML 1.0 no admite controles arbitrarios presentes en archivos importados.
        text = re.sub('[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]', '', text)
        props = ('<w:pageBreakBefore/>' if page else '')
        if heading:
            props += f'<w:pStyle w:val="Heading{heading}"/>'
        runs = '<w:br/>'.join(f'<w:t xml:space="preserve">{escape(line)}</w:t>' for line in text.split('\n'))
        return f'<w:p><w:pPr>{props}</w:pPr><w:r>{runs}</w:r></w:p>'

    paragraphs = [paragraph(data['title'], 1)]
    for i, doc in enumerate(docs):
        for j, block in enumerate(re.split(r'\n\s*\n', doc['content'])):
            heading = re.fullmatch(r'(#{1,3}) ([^\n]+)', block)
            paragraphs.append(paragraph(heading[2] if heading else block, len(heading[1]) if heading else 0, j == 0))
    namespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    document = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{namespace}"><w:body>{"".join(paragraphs)}<w:sectPr/></w:body></w:document>'
    styles = f'<w:styles xmlns:w="{namespace}">' + ''.join(
        f'<w:style w:type="paragraph" w:styleId="Heading{i}"><w:name w:val="heading {i}"/><w:pPr><w:outlineLvl w:val="{i-1}"/></w:pPr><w:rPr><w:b/><w:sz w:val="{36-i*4}"/></w:rPr></w:style>'
        for i in range(1, 4)) + '</w:styles>'
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        archive.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr('word/_rels/document.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        archive.writestr('word/document.xml', document)
        archive.writestr('word/styles.xml', styles)
    return output.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def export_project(store, project):
    data = store.snapshot(project)
    images = data.get('images', [])
    total = sum(len(d['content'].encode('utf-8')) for d in data['documents']) + sum(store.path(project, 'images', image['file']).stat().st_size for image in images)
    check(total <= 32_000_000, 'El proyecto supera 32 MB. Descargá las imágenes por separado y conservá una copia privada de la carpeta del proyecto.')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for i, doc in enumerate(data['documents']):
            # Nombres de entrada controlados; sin traversal ni colisiones.
            archive.writestr(f'{i+1:02d}-{doc["id"][:8]}.md', doc['content'])
        for image in data.get('images', []):
            archive.writestr('images/' + image['id'] + ('.png' if image['mime'] == 'image/png' else '.jpg'), store.path(project, 'images', image['file']).read_bytes())
        archive.writestr('manifest.json', json.dumps({
            'title': data['title'], 'purpose':data['purpose'], 'translation_config':data.get('translation_config',{}), 'documents': [
                {'file': f'{i+1:02d}-{d["id"][:8]}.md', **{k: d[k] for k in ('name', 'role', 'synopsis', 'pov', 'stage', 'translation', 'translation_status') if k in d}}
                for i, d in enumerate(data['documents'])], 'word_goal': data.get('word_goal', 0),
                'decisions': data['decisions'], 'images': data.get('images', [])}, ensure_ascii=False, indent=2))
    check(output.tell() <= 32_000_000, 'El ZIP supera 32 MB. Descargá las imágenes por separado y conservá una copia privada de la carpeta del proyecto.')
    return output.getvalue(), 'application/zip'
