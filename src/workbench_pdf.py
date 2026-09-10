"""PDF de lectura local con paginación, fuente Unicode y medidas de la maqueta."""
import io
import re
from pathlib import Path
from xml.sax.saxutils import escape
from src.workbench_store import check


def export_pdf(data, documents):
    try:
        import reportlab
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
    except ImportError:
        check(False, 'PDF requiere las dependencias de requirements.txt. Los instaladores las incluyen.')
    for name, file in [('Workbench', 'Vera.ttf'), ('WorkbenchBold', 'VeraBd.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(Path(reportlab.__file__).parent / 'fonts' / file)))
    pdfmetrics.registerFontFamily('Workbench', normal='Workbench', bold='WorkbenchBold')
    all_text = data['title'] + ''.join(d['content'] for d in documents)
    glyphs = pdfmetrics.getFont('Workbench').face.charToGlyph
    check(all(char.isspace() or ord(char) in glyphs for char in all_text),
          'La fuente PDF incluida no cubre todos los caracteres de esta obra. Exportá DOCX para elegir una fuente compatible.')
    production = data.get('production') or {}
    width, height = production.get('width', 152.4), production.get('height', 228.6)
    check(type(width) in (int, float) and type(height) in (int, float) and 80 <= width <= 300 and 100 <= height <= 400, 'Medidas PDF inválidas.')
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(width*mm, height*mm), rightMargin=16*mm, leftMargin=16*mm,
                            topMargin=18*mm, bottomMargin=18*mm, title=data['title'], author=production.get('author', ''))
    normal = ParagraphStyle('Body', fontName='Workbench', fontSize=10, leading=15, spaceAfter=9, splitLongWords=True)
    title = ParagraphStyle('Title', parent=normal, fontName='WorkbenchBold', fontSize=18, leading=24, spaceAfter=18)
    story = [Paragraph(escape(data['title']), title)]
    for document in documents:
        story.append(PageBreak())
        for block in re.split(r'\n\s*\n', document['content']):
            if not block.strip():
                continue
            heading = re.match(r'^(#{1,6}) ([^\n]+)$', block)
            text = escape(heading[2] if heading else block).replace('\n', '<br/>')
            text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph(text, title if heading else normal))
    def page_number(canvas, document):
        canvas.saveState()
        canvas.setFont('Workbench', 8)
        canvas.drawCentredString(width*mm/2, 9*mm, str(document.page))
        canvas.restoreState()
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return output.getvalue(), 'application/pdf'
