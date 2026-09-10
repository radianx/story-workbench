"""Compatibilidad de project.json, sin escribir durante la lectura."""
from copy import deepcopy

SCHEMA_VERSION = 1


def migrate_project(original):
    from src.workbench_store import check
    check(isinstance(original, dict), 'Formato de proyecto inválido.')
    version = original.get('schema_version', 0)
    check(type(version) is int and 0 <= version <= SCHEMA_VERSION,
          'Este proyecto requiere una versión más reciente de Story Workbench.')
    if version == SCHEMA_VERSION:
        return original
    data = deepcopy(original)
    data.setdefault('workflow', 'writing')
    data.setdefault('purpose', 'novel')
    data.setdefault('initial_idea', '')
    if 'conversations' not in data:
        end = data.get('history_start', 0)
        data['conversations'] = ([dict(id='legacy', title='Conversaciones anteriores',
                                      start=0, end=end, date=data['updated'], draft='')] if end else [])
    data['schema_version'] = SCHEMA_VERSION
    return data
