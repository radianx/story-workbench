"""Traducción con criterio humano y preparación de mundos; reutiliza documentos e historial."""
import json
import time
from workbench_store import check, text_value, digest, uid

PURPOSES = ('novel', 'translation', 'rpg')
GUIDES = {
    'novel': '',
    'translation': (
        'Este proyecto es una traducción literaria dirigida por su autor. Entrevistá sobre idioma y '
        'variante de origen/destino, lector, intención, registro, voz, ambigüedad, humor, dialecto, '
        'nombres y términos recurrentes. Una pregunta relevante por turno. No conviertas fidelidad '
        'literal en criterio único. Explicá qué gana y pierde cada alternativa y consultá al autor '
        'cuando cambie intención, subtexto o efecto. No corrijas defectos del original en silencio. '
        'El encargo y glosario explícitos mandan; si contradicen el texto, preguntá. Para producir '
        'traducciones revisables se usa la tarea Traducir y consultar matices; el chat no aprueba textos.'),
    'rpg': (
        'Modo extra: preparar un mundo para una mesa de rol, no escribir una novela ni jugar una partida. '
        'El director de juego decide el canon. Entrevistá de a una pregunta y avanzá rápido con lo útil '
        'para preparar: experiencia de mesa, tono y límites de contenido, sistema/edición o reglas propias, '
        'escala, lugar inicial, facciones con intereses, PNJ con deseos/secretos, reglas del mundo y sus costos, '
        'conflictos y ganchos abiertos. No impongas protagonistas, finales ni acciones a los jugadores. '
        'Proponé situaciones y consecuencias posibles, no un guion obligatorio. Separá lo público de los '
        'secretos del director dentro de las fichas, pero no afirmes controles de acceso. Si se pide rapidez, '
        'ofrecé un paquete provisional breve con mundo, tres PNJ, dos facciones, lugares, reglas y ganchos; '
        'etiquetá las suposiciones. No simules turnos, dados, iniciativa ni combate. No inventes reglas '
        'oficiales de D&D: pedí sistema/edición y material autorizado si hacen falta; cualquier regla inventada '
        'es casera y pendiente. No exijas estructura de libro ni un arco cerrado.')}

TRANSLATION_INSTRUCTION = (
    'Trabajá SOLO la unidad original indicada en el encargo de traducción. El resto de fuentes es contexto. '
    'Antes de traducir, examiná posibles pérdidas de intención: polisemia, ironía, tratamiento, dialecto, '
    'registro, doble sentido, ritmo o referencia cultural. Si una decisión relevante no está resuelta, '
    'devolvé una sola pregunta, una cita literal breve del original, y 2 o 3 alternativas con su efecto; '
    'draft debe quedar vacío. No repitas matices resueltos en los criterios aprobados, salvo contradicción '
    'nueva que debas explicar. Solo cuando alcance el criterio del autor, entregá la traducción completa '
    'de esa unidad en draft (sin notas incrustadas), con question y quote vacíos y options vacío. '
    'message explica brevemente las elecciones o la pregunta. Aun sin dudas detectadas, el borrador '
    'necesita revisión humana. No afirmes que no existen otros matices ni que el texto está aprobado.')

TRANSLATION_SCHEMA = {'type':'object', 'properties': {
    **{k:{'type':'string'} for k in ('message','question','quote','draft')},
    'options':{'type':'array','items':{'type':'object','properties':{
        'wording':{'type':'string'},'effect':{'type':'string'}},
        'required':['wording','effect'],'additionalProperties':False}}},
    'required':['message','question','quote','draft','options'],'additionalProperties':False}


def brief_hash(config):
    # La fuente cambia por unidad; idioma, voz y glosario pertenecen a la edición.
    return digest(json.dumps({k:v for k,v in config.items() if k != 'source'}, sort_keys=True))


def configure_translation(store, data, values):
    check(data['purpose']=='translation', 'Elegí el modo Traducción.')
    check(isinstance(values, dict), 'Encargo inválido.')
    config={k:text_value(values.get(k,''), limit, k not in ('source_language','target_language'))
            for k,limit in [('source_language',100),('target_language',100),('intent',4000),('glossary',6000)]}
    source=store.document(data, values.get('source'))
    check(not source.get('translation') and source['role']!='traducción', 'Elegí un original, no una traducción.')
    check(0 < len(source['content'].strip()) and len(source['content'])<=12000,
          'Elegí una unidad de hasta 12.000 caracteres. Importá fragmentos o capítulos cortos como copias.')
    config['source']=source['id']
    data.update(translation_config=config, thread=None, context_key=None)
    store.persist(data)


def translation_context(store, data, docs):
    config=data.get('translation_config',{})
    check(config.get('source') and config.get('target_language'), 'Completá el encargo en Traducción antes de comenzar.')
    source=next((d for d in docs if d['id']==config['source']),None)
    check(source is not None, 'Marcá el original del encargo como fuente para IA.')
    check(not source.get('translation') and source['role']!='traducción', 'La fuente debe ser un original.')
    check(0 < len(source['content'].strip()) and len(source['content'])<=12000, 'La unidad original debe tener entre 1 y 12.000 caracteres.')
    context=dict(source=source['id'], hash=source['hash'], original=source['content'], config=dict(config),
                 brief=brief_hash(config), criteria=digest(json.dumps(data['decisions'],sort_keys=True)))
    pending=[r for r in data['runs'] if r.get('translation_context',{}).get('source')==source['id']
             and r['translation_context'].get('hash')==source['hash']
             and r['translation_context'].get('brief')==context['brief']
             and r.get('translation_result',{}).get('question') and not r.get('translation_answer')]
    check(not pending, 'Registrá tu criterio en el matiz pendiente antes de continuar la traducción.',409)
    return context


def validate_translation(result, context):
    check(isinstance(result,dict), 'Respuesta de traducción inválida.')
    prepared={k:text_value(result.get(k), limit, k!='message') for k,limit in
              [('message',6000),('question',3000),('quote',2000),('draft',100000)]}
    options=result.get('options');check(isinstance(options,list) and len(options)<=3,'Alternativas inválidas.')
    prepared['options']=[]
    for option in options:
        check(isinstance(option,dict),'Alternativa inválida.')
        prepared['options'].append({k:text_value(option.get(k),3000,False) for k in ('wording','effect')})
    prepared['question']=prepared['question'].strip()
    if prepared['question']:
        check(not prepared['draft'].strip() and len(options)>=2 and prepared['quote'].strip()
              and prepared['quote'] in context['original'], 'Una consulta necesita cita del original y alternativas; no puede incluir traducción definitiva.')
    else:
        check(prepared['draft'].strip() and not prepared['quote'] and not options, 'Se necesita una consulta o un borrador revisable.')
    return prepared


def translation_run(data, run_id):
    run=next((r for r in data['runs'] if r['id']==run_id),None)
    check(run and run['status']=='completed' and run.get('translation_result'), 'Traducción no disponible.',409)
    return run


def current_source(store, data, context):
    source=store.document(data,context['source'])
    check(source['hash']==context['hash'], 'Cambió el original. Prepará otra traducción con su versión actual.',409)
    check(brief_hash(data.get('translation_config',{}))==context['brief'], 'Cambió el encargo o glosario. Prepará otra traducción.',409)
    return source


def answer_translation(store, data, run_id, answer):
    run=translation_run(data,run_id);context=run['translation_context']
    current_source(store,data,context)
    check(run['translation_result']['question'], 'Esta respuesta no tiene un matiz pendiente.')
    answer=text_value(answer,4000,False)
    if run.get('translation_answer'):
        check(run['translation_answer']==answer,'El criterio ya fue registrado.',409)
        return
    run['translation_answer']=answer
    data['decisions'].append(dict(id=uid(),status='accepted',date=time.time(),
        text='Criterio de traducción: '+run['translation_result']['question']+'\nDecisión del autor: '+answer,
        translation_source=context['source'],source_hash=context['hash'],target_language=context['config']['target_language']))
    store.persist(data)


def accept_translation(store, data, run_id, text):
    run=translation_run(data,run_id)
    check(run['translation_result']['draft'] and not run['translation_result']['question'], 'Resolvé primero el matiz; todavía no hay borrador.')
    # La misma aprobación nunca crea otra copia ni pisa cambios manuales posteriores.
    existing=next((d for d in data['documents'] if d.get('source_run')==run_id),None)
    if existing:
        check(existing.get('translation'), 'Revisá la copia recuperada antes de aprobar.',409)
        return store.document(data,existing['id'])
    context=run['translation_context'];source=current_source(store,data,context)
    check(digest(json.dumps(data['decisions'],sort_keys=True))==context['criteria'], 'Hay criterios nuevos desde este borrador. Pedí una revisión con ellos.',409)
    text=text_value(text,empty=False)
    name=(source['name'].removesuffix('.md')[:110]+' · '+context['config']['target_language'][:60]+'.md')
    document=store.add_document(data['id'],name,'traducción',text,selected=False,source_run=run_id,
                               translation=dict(source=context['source'],hash=context['hash'],brief=context['brief'],
                                                target_language=context['config']['target_language'],review_hash=digest(text)))
    return document


def translation_status(store,data,doc):
    link=doc['translation']
    source=next((d for d in data['documents'] if d['id']==link['source']),None)
    source_hash=store.document(data,source['id'])['hash'] if source else None
    return ('reviewed' if source_hash==link['hash'] and doc['hash']==link['review_hash']
            and brief_hash(data.get('translation_config',{}))==link['brief'] else 'revise')


def review_translation(store,data,document,expected,source_expected):
    doc=store.document(data,document);check(doc.get('translation'),'Elegí una traducción vinculada.')
    source=store.document(data,doc['translation']['source'])
    check(doc['hash']==expected and source['hash']==source_expected,'El texto cambió desde que abriste la revisión.',409)
    check(doc['content'].strip(),'Una traducción vacía no puede aprobarse.')
    config=data.get('translation_config',{})
    check(doc['translation']['target_language']==config.get('target_language'),'El idioma de esta traducción no corresponde al encargo actual.')
    meta=next(d for d in data['documents'] if d['id']==document)
    meta['translation'].update(hash=source['hash'],review_hash=doc['hash'],brief=brief_hash(config))
    data['decisions'].append(dict(id=uid(),text='Revisión humana de traducción: '+doc['name'],status='accepted',date=time.time(),
                                  translation_source=source['id'],source_hash=source['hash'],target_hash=doc['hash']))
    store.persist(data)


def translation_edition(data):
    locale=data.get('translation_config',{}).get('target_language')
    latest={}
    for doc in data['documents']:
        if doc.get('translation',{}).get('target_language')==locale:
            latest[doc['translation']['source']]=doc
    check(latest,'No hay traducciones aprobadas para este idioma.')
    check(all(d.get('translation_status')=='reviewed' for d in latest.values()), 'Hay traducciones por revisar. Abrí Traducción antes de exportar.',409)
    docs=[{**latest[d['id']],'role':'manuscrito'} for d in data['documents'] if d['id'] in latest]
    return {'title':data['title']+' · '+locale,'documents':docs}
