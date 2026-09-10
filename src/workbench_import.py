"""Importación local de texto; ZIP se lee en memoria, nunca se extrae ni ejecuta."""
import base64
import io
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET
from src.workbench_store import check, text_value, MAX_TEXT

MAX_FILE = 15_000_000
MAX_EXPANDED = 40_000_000
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def xml(data):
    check(not re.search(br'<!\s*(DOCTYPE|ENTITY)', data.replace(b'\0', b''), re.I), 'XML con entidades no permitido.')
    return ET.fromstring(data)


class BookText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        tag = tag.rsplit(':', 1)[-1].lower()
        if tag in ('head', 'script', 'style', 'svg'):
            self.hidden += 1
        if self.hidden:
            return
        if tag in ('p', 'div', 'section', 'article', 'blockquote', 'tr'):
            self.parts.append('\n\n')
        elif re.fullmatch('h[1-6]', tag):
            self.parts.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag == 'li':
            self.parts.append('\n- ')
        elif tag == 'br':
            self.parts.append('\n')
        elif tag in ('td', 'th'):
            self.parts.append(' | ')

    def handle_endtag(self, tag):
        tag = tag.rsplit(':', 1)[-1].lower()
        if tag in ('head', 'script', 'style', 'svg'):
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden and (tag in ('p', 'div', 'section', 'article', 'blockquote', 'tr') or re.fullmatch('h[1-6]', tag)):
            self.parts.append('\n\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(re.sub(r'\s+', ' ', data))

    def text(self):
        return re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', ''.join(self.parts)).strip()


def documents(name, text):
    check(text.strip(), 'El archivo no contiene texto importable.')
    # División reversible por caracteres UTF-8, incluso para idiomas multibyte.
    parts = []
    while text:
        part = text.encode('utf-8')[:MAX_TEXT].decode('utf-8', errors='ignore')
        parts.append(part)
        text = text[len(part):]
    return [dict(name=name if len(parts) == 1 else f"{name.encode('utf-8')[:160].decode('utf-8', errors='ignore')} · Parte {i+1}", content=part, role='manuscrito')
            for i, part in enumerate(parts)]


def import_file(name, encoded):
    text_value(name, 200, False)
    check(isinstance(encoded, str) and len(encoded) <= MAX_FILE * 4 // 3 + 4, 'Archivo demasiado grande: máximo 15 MB.')
    try:
        data = base64.b64decode(encoded, validate=True)
        check(0 < len(data) <= MAX_FILE, 'Archivo vacío o demasiado grande.')
        extension = PurePosixPath(name).suffix.lower()
        if extension in ('.md', '.markdown', '.txt'):
            text = data.decode('utf-8-sig')
            text_value(text, MAX_EXPANDED, False)
            result = documents(name, text)
            check(len(result) <= 100, 'El texto supera 100 unidades.')
            return dict(documents=result, warnings=[])
        check(extension in ('.docx', '.epub'), 'Usá Markdown, TXT, DOCX o EPUB.')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            check(len(entries) <= 2000 and sum(e.file_size for e in entries) <= MAX_EXPANDED, 'El contenido descomprimido supera el límite.')
            names = [e.filename for e in entries]
            check(len(set(names)) == len(names), 'Archivo con entradas duplicadas.')
            for entry in entries:
                path = PurePosixPath(entry.filename)
                check(not path.is_absolute() and '..' not in path.parts and '\\' not in entry.filename and not entry.flag_bits & 1,
                      'Archivo protegido o con rutas inválidas.')
            result = read_docx(archive, name) if extension == '.docx' else read_epub(archive)
        check(0 < len(result) <= 100, 'La obra debe producir entre 1 y 100 documentos; importá una parte.')
        for document in result:
            text_value(document['content'], empty=False)
        return dict(documents=result, warnings=['Se importó el texto para revisión. No se copian imágenes, diseño de página ni comentarios; los originales permanecen intactos.'])
    except (zipfile.BadZipFile, ET.ParseError, KeyError, UnicodeError, ValueError, RuntimeError) as error:
        raise ValueError('No se pudo leer el archivo. Verificá que sea un DOCX/EPUB válido, sin protección, o texto UTF-8.') from error


def read_docx(archive, name):
    root = xml(archive.read('word/document.xml'))
    body = root.find(W + 'body')
    check(body is not None, 'DOCX sin cuerpo de texto.')

    def text(element):
        if element.tag == W + 'del':
            return ''
        if element.tag == W + 'p':
            return ''.join(text(child) for child in element) + '\n'
        if element.tag == W + 't':
            return element.text or ''
        if element.tag in (W + 'br', W + 'cr'):
            return '\n'
        if element.tag == W + 'tab':
            return '\t'
        if element.tag in (W + 'footnoteReference', W + 'endnoteReference'):
            return f" [nota {element.get(W+'id', '')}]"
        return ''.join(text(child) for child in element)

    blocks = []
    for node in body:
        if node.tag == W + 'p':
            value = text(node).strip()
            style = node.find('./' + W + 'pPr/' + W + 'pStyle')
            heading = re.search(r'(?:heading|titulo|título)([1-6])', style.get(W+'val', ''), re.I) if style is not None else None
            if heading:
                value = '#' * int(heading[1]) + ' ' + value
            elif node.find('./' + W + 'pPr/' + W + 'numPr') is not None:
                value = '- ' + value
            blocks.append(value)
        elif node.tag == W + 'tbl':
            blocks.append('\n'.join(' | '.join(text(cell).replace('\n', ' ') for cell in row.findall(W+'tc'))
                                    for row in node.findall(W+'tr')))
    for file in ('word/footnotes.xml', 'word/endnotes.xml'):
        if file in archive.namelist():
            for note in xml(archive.read(file)):
                if note.get(W+'type') not in ('separator', 'continuationSeparator'):
                    blocks.append(f"[nota {note.get(W+'id', '')}] {text(note)}")
    return documents(name, '\n\n'.join(blocks).strip())


def read_epub(archive):
    container = xml(archive.read('META-INF/container.xml'))
    rootfile = container.find('.//{*}rootfile')
    check(rootfile is not None, 'EPUB sin índice de contenido.')
    opf = rootfile.get('full-path', '')
    check(opf in archive.namelist(), 'Índice EPUB inválido.')
    package = xml(archive.read(opf))
    manifest = {item.get('id'): item for item in package.findall('./{*}manifest/{*}item')}
    encrypted = set()
    if 'META-INF/encryption.xml' in archive.namelist():
        encrypted = {unquote(item.get('URI', '')) for item in xml(archive.read('META-INF/encryption.xml')).iter() if item.tag.endswith('CipherReference')}
    result = []
    for itemref in package.findall('./{*}spine/{*}itemref'):
        item = manifest.get(itemref.get('idref'))
        check(item is not None and item.get('media-type') in ('application/xhtml+xml', 'text/html'), 'EPUB con contenido de lectura no compatible.')
        url = urlsplit(item.get('href', ''))
        path = posixpath.normpath(posixpath.join(posixpath.dirname(opf), unquote(url.path)))
        check(not url.scheme and not url.netloc and not path.startswith(('/', '../')) and path in archive.namelist(), 'Referencia EPUB inválida.')
        check(path not in encrypted, 'El texto EPUB está protegido; usá una copia sin DRM.')
        parser = BookText()
        parser.feed(archive.read(path).decode('utf-8-sig'))
        text = parser.text()
        if text:
            result.extend(documents(f"{len(result)+1:02d} · {PurePosixPath(path).stem.encode('utf-8')[:160].decode('utf-8', errors='ignore')}", text))
    return result
