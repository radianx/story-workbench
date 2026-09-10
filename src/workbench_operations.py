"""Operaciones editoriales independientes del transporte HTTP."""
from src.workbench_store import Problem, check, text_value, ROLES, WORKFLOWS
from src.workbench_workspace import import_documents, import_preview
import src.workbench_modes as modes


def project_operation(services, path, body):
    store = services.store
    with store.lock:
        if path == '/api/projects':
            documents=body.get('documents')
            if body.get('import_folder') is not None:
                folder=body['import_folder'];check(isinstance(folder,dict) and documents is None,'Importación inválida.')
                documents=import_documents(folder.get('path'),folder.get('files'))
            result = store.create(body.get('title'), bool(body.get('demo')),
                                  body.get('workflow', 'writing'), body.get('initial_idea', ''), body.get('purpose','novel'),
                                  documents, body.get('translation'))
        elif path == '/api/import/preview':
            result=import_preview(body.get('path'))
        elif path == '/api/translation/detect':
            content=body.get('text')
            if body.get('path') is not None:
                content=import_documents(body.get('path'),[body.get('file')])[0]['content']
            result=dict(language=modes.detect_language(content))
        elif path == '/api/workspace':
            result=services.workspace.choose(body.get('path'),body.get('name',''))
        else:
            project = body.get('project')
            data = store.load(project)
            if path == '/api/document/import':
                store.add_documents(data, body.get('documents'));result=store.snapshot(project)
            elif path == '/api/project/archive':
                check(not body.get('archived') or not services.assistant.active or services.assistant.active[0]!=project,
                      'Esperá a que termine la tarea antes de archivar el proyecto.',409)
                store.archive_project(data,body.get('archived'));result={'ok':True}
            elif path == '/api/project/purpose':
                check(not services.assistant.active,'Esperá a que termine la tarea.',409)
                check(body.get('purpose') in modes.PURPOSES,'Objetivo inválido.')
                data.update(purpose=body['purpose'],thread=None,context_key=None)
                if data['purpose']!='novel':data['workflow']='guided'
                store.persist(data);result=store.snapshot(project)
            elif path == '/api/translation/config':
                check(not services.assistant.active,'Esperá a que termine la tarea.',409)
                modes.configure_translation(store,data,body.get('config'));result=store.snapshot(project)
            elif path == '/api/translation/answer':
                modes.answer_translation(store,data,body.get('run'),body.get('answer'));result=store.snapshot(project)
            elif path == '/api/translation/accept':
                result=modes.accept_translation(store,data,body.get('run'),body.get('text'))
            elif path == '/api/translation/review':
                modes.review_translation(store,data,body.get('document'),body.get('hash'),body.get('source_hash'));result=store.snapshot(project)
            elif path == '/api/project/goal':
                goal = body.get('goal')
                check(type(goal) is int and 0 <= goal <= 2_000_000, 'Meta inválida: entre 0 y 2.000.000 palabras.')
                data['word_goal'] = goal
                store.persist(data)
                result = store.snapshot(project)
            elif path == '/api/project/order':
                store.reorder(data, body.get('order'))
                result = store.snapshot(project)
            elif path == '/api/document/planning':
                store.planning(data, body.get('document'), body.get('planning'))
                result = store.snapshot(project)
            elif path == '/api/run/save-draft':
                result = store.save_draft(data, body.get('run'))
            elif path == '/api/project/engine':
                from src.workbench_providers import engine_preferences
                check(not services.assistant.active, 'Esperá a que termine la tarea antes de cambiar de motor.',409)
                data['engine'] = engine_preferences(body.get('engine'))
                data.update(thread=None,context_key=None)
                store.persist(data)
                result=store.snapshot(project)
            elif path == '/api/project/team':
                from src.workbench_team import team_preferences
                from src.workbench_account import resolve_ai
                check(not services.assistant.active, 'Esperá a que termine la tarea.',409)
                preferences=team_preferences(body.get('preferences'))
                resolve_ai(preferences,services.account.snapshot().get('models',[]))
                data['team_preferences']=preferences;store.persist(data);result=store.snapshot(project)
            elif path == '/api/project/ai':
                from src.workbench_account import ai_preferences, resolve_ai
                preferences = ai_preferences(body.get('preferences'))
                resolve_ai(preferences, services.account.snapshot().get('models', []))
                data['ai_preferences'] = preferences
                store.persist(data)
                result = store.snapshot(project)
            elif path == '/api/project/production':
                from src.workbench_production import validate_production
                data['production'] = validate_production(body.get('production'))
                store.persist(data)
                result = store.snapshot(project)
            elif path == '/api/project/workflow':
                check(body.get('workflow') in WORKFLOWS, 'Forma de trabajo inválida.')
                data['workflow'] = body['workflow']
                store.persist(data)
                result = store.snapshot(project)
            elif path == '/api/interview/start':
                check(type(body.get('retry', False)) is bool, 'Reintento inválido.')
                result = services.assistant.start_interview(project, body.get('retry', False))
            elif path == '/api/document/add':
                result = store.add_document(project, body.get('name'), body.get('role'), body.get('content'), body.get('selected', True))
            elif path == '/api/document/save':
                result = store.save_document(data, body.get('document'), body.get('content'), body.get('hash'))
            elif path == '/api/document/meta':
                store.document(data, body.get('document'))
                doc = next(d for d in data['documents'] if d['id'] == body['document'])
                if 'selected' in body:
                    check(type(body['selected']) is bool, 'Selección inválida.')
                    doc['selected'] = body['selected']
                if 'role' in body:
                    check(body['role'] in ROLES, 'Rol inválido.')
                    doc['role'] = body['role']
                if 'name' in body:
                    doc['name'] = text_value(body['name'], 200, False)
                store.persist(data)
                result = store.snapshot(project)
            elif path == '/api/document/restore':
                current = store.document(data, body.get('document'))
                version = next((v for v in current['history'] if v['id'] == body.get('version')), None)
                check(version is not None, 'Versión no encontrada.', 404)
                content = store.path(project, 'history', version['id'] + '.md').read_text(encoding='utf-8')
                result = store.save_document(data, current['id'], content, body.get('hash'), 'Restauración de versión')
            elif path == '/api/proposal/decide':
                check(type(body.get('accept')) is bool, 'Decisión inválida.')
                result = store.decide(project, body.get('proposal'), body['accept'])
            elif path == '/api/decision':
                check(body.get('status') in ('accepted', 'pending', 'rejected'), 'Estado inválido.')
                from src.workbench_store import uid
                import time
                data['decisions'].append(dict(id=uid(), text=text_value(body.get('text'), 4000, False),
                                              status=body['status'], date=time.time()))
                store.persist(data)
                result = store.snapshot(project)
            elif path == '/api/thread/reset':
                check(not services.assistant.active, 'Esperá a que termine la tarea.', 409)
                store.reset_conversation(data,body.get('draft',''))
                result = store.snapshot(project)
            elif path == '/api/run':
                result = services.assistant.start(project, body.get('mode'),
                    text_value(body.get('prompt'), 10_000, False), body.get('skill', True), body.get('team',False))
            elif path == '/api/run/cancel':
                services.assistant.stop(project, body.get('run'))
                result = {'ok': True}
            else:
                raise Problem('Ruta no encontrada.', 404)
    return result
