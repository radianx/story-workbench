"""Maqueta visual local; medidas declaradas por el autor, no plantilla de imprenta."""
import base64
import math
from workbench_store import check, text_value


def validate_production(value):
    check(isinstance(value, dict), 'Maqueta inválida.')
    result = {}
    for key, low, high in (('width', 80, 300), ('height', 100, 400), ('spine', .01, 100)):
        number = value.get(key)
        check(type(number) in (int, float) and math.isfinite(number) and low <= number <= high,
              'Medidas fuera de rango.')
        result[key] = number
    sizing = value.get('sizing', 'manual')
    check(sizing in ('manual', 'pages', 'estimate'), 'Cálculo de lomo inválido.')
    paper, pages = value.get('paper', 'white'), value.get('pages', 24)
    check(paper in ('white', 'cream'), 'Papel inválido.')
    check(type(pages) is int and 1 <= pages <= 1500, 'Usá entre 1 y 1500 páginas.')
    result.update(sizing=sizing, paper=paper, pages=pages)
    if sizing != 'manual':
        # KDP tapa blanda, interior blanco y negro: mm por página, no por hoja.
        result['spine'] = round(pages * (.0635 if paper == 'cream' else .0572), 2)
    for key in ('title', 'author'):

        result[key] = text_value(value.get(key, ''), 300)
    for key in ('front', 'back', 'spineImage'):
        image = text_value(value.get(key, ''), 410_000)
        if image:
            prefix, _, encoded = image.partition(',')
            check(prefix == 'data:image/jpeg;base64', 'Se requiere una imagen JPEG local.')
            try:
                raw = base64.b64decode(encoded, validate=True)
            except ValueError:
                check(False, 'Imagen inválida.')
            check(raw.startswith(b'\xff\xd8\xff') and raw.endswith(b'\xff\xd9'), 'Imagen inválida.')
        result[key] = image
    return result
