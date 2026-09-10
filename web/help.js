'use strict';
// Ayuda propia, incluida con la app: no carga páginas externas ni llama al asistente.
const helpTopics = [
  ['interview','Empezar y continuar la entrevista',[
    'El asistente inicial aparece una vez, permite omitirlo y se reabre desde Configuración. Podés conectar cuentas, preparar claves opcionales y crear o abrir un proyecto. Ctrl/Cmd+K abre Ir a una sección; Ctrl/Cmd+, abre Configuración. Tab y Shift+Tab recorren controles y las flechas cambian pestañas. La voz online permite navegar después de conectarla; claves, permisos y aprobaciones editoriales siguen bajo control manual.',
    'Elegí Crear mi proyecto y Crear conversando. Una idea incompleta alcanza: el agente pregunta de a una. Si falta conectar ChatGPT, la app te muestra el acceso a tu cuenta.',
    'Respondé en el mensaje o usá Dictar respuesta. Enviar inicia el trabajo y consume tu cuota de Codex. Podés detener una tarea sin convertir su respuesta en material aprobado.',
    'Cuando quieras avanzar, cambiá Tipo de tarea a Redactar borrador. Guardar como borrador provisional crea un documento nuevo únicamente cuando lo elegís. Ver material abre el editor; Ocultar material devuelve espacio al chat.',
    'Nueva conversación vacía el chat y reinicia su contexto. Las fuentes y decisiones siguen disponibles; consultá los chats anteriores en el desplegable debajo del botón. La forma de trabajo se cambia desde Configuración.'
  ]],
  ['sources','Fuentes, biblioteca y fichas',[
    'Archivar proyecto lo quita de Tu biblioteca conservando documentos, conversaciones e historial en su carpeta. Proyectos archivados, en la biblioteca, Inicio o Configuración, permite restaurarlo. Primero guardá los cambios y terminá cualquier tarea en curso.',
    'Las casillas junto a los documentos eligen qué texto recibe el asistente. Abrir un documento para leerlo no lo selecciona para IA. Para hablar de una fuente, marcala y guardá sus cambios primero.',
    'Cambiar la selección abre un hilo nuevo en el próximo envío para retirar el contexto anterior. La idea inicial y las decisiones del proyecto también se envían. Máximo: 60.000 caracteres de fuentes y sus fichas del plan; no se recortan en silencio.',
    'Importar copias admite Markdown y TXT en UTF-8, hasta 250 KB por archivo. Los originales permanecen en su lugar. Los archivos importados quedan seleccionados; revisá las casillas antes de enviar.',
    'Importar carpeta, desde Inicio o Configuración, muestra los Markdown/TXT y permite elegir cuáles copiar en un proyecto nuevo. Conserva sus rutas relativas en los nombres; reconoce manuscript/manuscrito como material del libro, y deja el resto como referencias. Las copias de carpeta no se seleccionan para IA salvo la primera unidad de traducción. Imágenes, PDF, DOCX, archivos ocultos y enlaces quedan fuera.',
    'Configuración → Carpeta de trabajo permite elegir una carpeta vacía o un espacio de la app, o crear una subcarpeta. El cambio se recuerda y se usa al reiniciar; no traslada proyectos existentes ni cuentas. Para recuperar otra biblioteca, volvé a elegir su ubicación. Para una carpeta de manuscritos, usá Importar carpeta.',
    'Ficha de historia crea una plantilla de personaje, mundo, voz o arco. Empieza como documento provisional sin seleccionar para IA. Completala y seleccioná su casilla cuando quieras compartirla.',
    'Tipos: Manuscrito forma el libro exportado; Canon contiene hechos establecidos por vos; Voz y estilo orienta la prosa; Planificación organiza ideas; Referencia aporta material de apoyo; Traducción conserva otro idioma. El tipo no aprueba automáticamente el contenido.'
  ]],
  ['models','Cuenta, modelo y esfuerzo',[
    'Cuenta ChatGPT abre el inicio de sesión en tu navegador. Cada autor usa su propia cuenta. La escritura local funciona sin iniciar sesión; el asistente necesita internet y cuota disponible. Las tareas de Codex no usan claves API ni cambian a pago. Realtime es una opción separada y explícita.',
    'Elegí Modelo y Esfuerzo debajo del mensaje, junto al tipo de tarea. Para cambiar de proveedor, abrí Configuración → Inteligencia artificial. Los motores experimentales muestran un acceso a su modelo en el chat. Se guardan por proyecto y se aplican al próximo mensaje. Solo aparecen opciones compatibles que devuelve tu cuenta. Actualizar modelos vuelve a consultar su disponibilidad.',
    'Un esfuerzo mayor puede tardar más; no garantiza mejor voz literaria. Si un modelo guardado deja de estar disponible, elegí otro. La app no lo sustituye en silencio.',
    'Elegir motor editorial permite mantener Codex con ChatGPT o usar OpenAI API, Gemini, Anthropic, DeepSeek, Kimi o un servidor local compatible. Los seis adaptadores alternativos son experimentales, requieren ID de modelo y clave propia salvo local, usan esfuerzo predeterminado y no cambian de proveedor ante errores. Se recuerda el motor por proyecto y las claves pueden cifrarse fuera de los proyectos.',
    'La guía editorial usa build-novel si está instalada, o la guía integrada cuando no está disponible. No necesitás instalar una skill para empezar.'
  ]],
  ['voice','Dictado, micrófono y lectura en voz alta',[
    'El micrófono junto a Enviar alterna la captura con cada clic. También podés mantener Espacio para hablar y soltar para terminar, si el mensaje está vacío. Con texto escrito, Espacio escribe normalmente. Podés descartar el dictado; cada captura admite hasta 45 segundos. La transcripción aparece en el mensaje para corregirla antes de Enviar. Los nombres propios pueden necesitar correcciones.',
    'En Dictar respuesta, el audio se procesa localmente en español, permanece solo en memoria y no se envía a ChatGPT. El micrófono se apaga al terminar, descartar o cambiar de proyecto. Enviar comparte el texto del mensaje con el asistente.',
    'Escuchar usa el proveedor de voz online si está habilitado y autorizado; si falta o falla, usa la voz local. En Configuración → Voz y lectura podés elegir Siempre voz local y ajustar Volumen de voz. El volumen se guarda, afecta tanto al asistente online como a la lectura local y permite silenciarlos con 0%. La lectura no abre el micrófono y cierra una conversación oral activa. Detener lectura la interrumpe. La casilla Leer respuestas junto al micrófono es opcional y se desactiva al cambiar de proyecto; no reproduce todo el historial.',
    'Configuración → Voz y lectura → Probar voz del proveedor envía una frase de prueba sin abrir el micrófono ni usar respaldo local. Requiere clave y permisos guardados. Muestra conexión, fragmentos, segundos de audio, señal y estado del reproductor. Si no llega señal, no afirma que se haya escuchado voz. Detener prueba cancela la conexión.',
    'Si no funciona el micrófono, revisá el permiso de la app o navegador y el dispositivo de entrada del sistema. Si indica que falta el motor, usá el instalador con voz. Si falta lectura, revisá las voces instaladas de Windows o la instalación del paquete Linux. Siempre podés responder por escrito.'
  ]],
  ['realtime','Asistente de voz: Gemini Live / OpenAI y acciones',[
    'Abrí Configuración (la tuerca), luego Asistente de voz, activalo y elegí proveedor: OpenAI (gpt-realtime) o Google (gemini-3.1-flash-live-preview). Ingresá la clave correspondiente. Gemini usa la de Google AI Studio y no necesita una clave OpenAI. AI Plus no determina la cuota de esa API: revisá el proyecto de la clave. OpenAI Realtime no funciona con la sesión ChatGPT de esta versión de Codex. Nunca se cambia de proveedor automáticamente.',
    'Por defecto la clave dura esta ejecución. En escritorio podés elegir Recordar para cifrarla con el almacén del sistema, fuera de los proyectos. Si no hay almacén seguro, solo se permite memoria. Olvidar clave elimina ambas copias. No la ingreses en el chat. Cada ventana pide consentimiento para enviar audio, biblioteca, fuentes seleccionadas, criterios y hasta ocho turnos compatibles al proveedor elegido. La API puede generar cargos. En el nivel gratuito de Gemini, Google puede usar contenido para mejorar sus productos. Al cambiar proveedor se vuelve a pedir consentimiento. Conecta al pulsar el micrófono del chat o mantener Espacio.',
    'El clic alterna escucha continua y pausa. Mantener Espacio abre la escucha hasta soltar; la respuesta puede seguir sonando. Salir de la ventana cierra la escucha iniciada con Espacio. Podés interrumpir hablando o terminar la conexión. Si habilitás acciones, puede abrir secciones y documentos, cambiar tema, preparar mensajes o criterios pendientes y lanzar tareas de Codex. Las tareas consumen también cuota Codex y sus resultados quedan en el chat para revisar. Aprobar textos o registrar decisiones requiere tu acción manual.',
    'La conversación oral es temporal: no se guarda como entrevista completa. Pedí iniciar una tarea de entrevista con Codex o preparar una decisión para conservar lo relevante. Podés pedir que consulte el resultado cuando termine. No reemplaza mensajes sin enviar ni cambios pendientes del editor.',
    'Cambiar proyecto, fuentes o permisos cierra la conexión. Terminar cierra micrófono y audio; pausar el micrófono mantiene la conexión y no es un control de gasto. Cada conexión termina a los 10 minutos, sin reconexión automática. El límite de tiempo no es un presupuesto: administrá cuota y saldo en la plataforma API.'
  ]],
  ['review','Diagnosticar, proponer y aceptar cambios',[
    'Diagnosticar señala problemas sin reescribir. Analizar impacto explora qué podría afectar un cambio hipotético. Proponer cambios prepara bloques antes/después que todavía no modifican el manuscrito.',
    'En Propuestas podés aceptar o rechazar cada bloque. Aceptarlo cambia la copia local, conserva una versión anterior y resalta el texto aplicado. Si el documento cambió, pedí una propuesta nueva: no se sobrescribe una versión distinta.',
    'Para revertir una aceptación, abrí el documento y usá Historial → Restaurar. Esto restaura la versión completa, no solo un bloque; conservamos también la versión que reemplaza. El registro editorial no se borra.',
    'Nuevo resalta una respuesta que aún no marcaste como vista. Podés colapsarla o marcarla como vista sin aprobar su contenido.'
  ]],
  ['decisions','Decisiones, ideas y canon',[
    'En Decisiones elegí Aprobada, Pendiente o Rechazada al registrar una nota. Una idea dicha en el chat no se convierte por sí sola en un hecho del universo.',
    'Separá alternativas de decisiones definitivas. El rol Canon ayuda a identificar un documento, pero no verifica su coherencia ni decide por vos.',
    'Resumir para retomar produce una referencia provisional. Al guardarla, incluye sus fuentes de origen: verificá que sigan vigentes antes de usarla como base.'
  ]],
  ['plan','Plan y barras de avance',[
    'Una tarjeta representa un documento de manuscrito, sea capítulo o escena. Las flechas cambian su orden, que también se usa al exportar el libro. Si importaste un libro entero como un documento, tendrá una sola tarjeta.',
    'La sinopsis y el punto de vista son orientaciones provisionales. Guardar ficha conserva esos datos; Preparar con IA escribe una petición editable, pero no la envía.',
    'La meta cuenta palabras guardadas; 0 significa sin meta. Revisado marca una versión concreta del texto. Si ese contenido cambia, vuelve a necesitar revisión. El contador mide documentos, no calidad literaria.',
    'La barra del asistente representa cuatro etapas de esa tarea: conexión, contexto, generación y comprobación. No es el porcentaje del libro ni una estimación de tiempo.'
  ]],
  ['recovery','Guardar, deshacer y recuperar texto',[
    'Guardar conserva el texto en este equipo. Cada cambio guardado mantiene una versión anterior en Historial. El borrador de la pestaña ayuda a recuperar cambios sin guardar, pero no reemplaza una copia de seguridad.',
    'Deshacer/Rehacer sirve para texto y formato del documento abierto, incluso después de guardar. Al cambiar de documento o recargar, usá Historial para recuperar versiones guardadas. Restaurar reemplaza el documento completo y conserva la versión actual.',
    'Si aparece otra versión del documento, tu borrador permanece en el editor. Descargalo antes de Recargar documento si querés conservarlo.',
    'El mensaje aún no enviado y su tipo de tarea se conservan por proyecto durante la sesión de esta ventana. Abrir Ayuda no borra el mensaje ni el borrador del editor. Cerrarlos sin haberlos guardado o enviado no es una copia de seguridad permanente.'
  ]],
  ['export','Exportar el libro o el proyecto',[
    'Descargar Markdown en el editor exporta el documento abierto, incluido su borrador sin guardar. Para exportar el libro completo, abrí Plan y avance y elegí Markdown o DOCX.',
    'El libro usa únicamente los documentos de tipo Manuscrito, guardados y en el orden del plan. Las casillas de contexto IA no deciden qué entra en el libro. DOCX conserva títulos y párrafos; otras marcas Markdown quedan como texto.',
    'Exportar proyecto genera un ZIP de documentos guardados y un manifiesto con nombres, tipos, fichas del plan, meta y decisiones. No incluye conversaciones, historial de versiones, imágenes de maqueta ni sesión ChatGPT; no es una copia completa de toda la app.',
    'La app todavía no reimporta ese ZIP como proyecto ni prepara EPUB/PDF de imprenta. Conservá tus exportaciones en un lugar elegido por vos.'
  ]],
  ['production','Tema, ambiente, foco y libro 3D',[
    'El asistente inicial empieza por el tema. En él y en Configuración tenés una sola lista: Sistema (inicial), claros salvia/celeste/crema/rosado y oscuros salvia/violeta/rojo/azul; también Neón y Vice City en ambos modos. Personalizar o compartir un tema permite editar colores e importar/exportar JSON. La opacidad de la imagen de ambiente se ajusta y recuerda desde Configuración. La elección se recuerda incluso si omitís el asistente. El icono sol/luna cambia rápidamente entre claro y oscuro. Ambiente es otra cosa: una imagen tenue detrás del editor, local a esta pestaña. No se envía al asistente y se retira al cambiar de proyecto.',
    'Modo foco oculta paneles secundarios. En creación guiada prioriza el chat; en escritura prioriza el documento. Salir de foco recupera los paneles sin detener una tarea.',
    'Libro 3D es una maqueta visual de portada, lomo, contraportada y páginas. Usá las medidas y el grosor que confirme tu imprenta. Por defecto usa 6 × 9 pulgadas y estima páginas del manuscrito guardado; podés ingresar la paginación real y elegir papel blanco o crema, o indicar un lomo manual. La estimación no sustituye la maquetación.',
    'Guardar maqueta conserva medidas y copias de las imágenes en el proyecto. Girar el libro solo cambia la vista. La maqueta no es una cubierta técnica lista para imprimir.'
  ]],
  ['translation','Traducción literaria: intención y revisión humana',[
    'Elegí Traducción literaria al crear un proyecto o en Objetivo. En un proyecto nuevo, importá primero la obra y elegí idioma original y destino. La detección local sugiere un idioma que podés corregir; no detecta variantes. La entrevista continúa con lector, voz e intención. En Traducción podés ajustar el encargo y glosario.',
    'Trabajamos una unidad de hasta 12.000 caracteres por turno, más las fuentes de apoyo seleccionadas. El wizard divide el original elegido en unidades de hasta 12.000 caracteres sin omitir texto; solo la primera queda seleccionada para IA. Las demás unidades requieren elegirlas en el encargo y marcarlas como fuentes. Otros archivos son referencias sin seleccionar.',
    'Traducir y consultar matices puede mostrar una cita, una pregunta y alternativas con sus efectos. Elegí una, corregila o escribí otro criterio. Registrar mi criterio guarda una decisión del autor; Continuar con IA consume otro turno. No permite saltar un matiz pendiente del mismo original y encargo.',
    'Cuando hay borrador, compará original congelado y traducción editable. Revisé y apruebo crea una copia de tipo Traducción sin modificar el original. Podés corregir el texto antes de aprobar; un borrador del chat nunca se acepta por sí solo.',
    'Si cambia el original, el texto traducido o el encargo, la copia requiere revisión. En Traducción podés comparar ambas versiones actuales, editar la copia y volver a aprobarlas. Cambiar de unidad dentro del mismo encargo no invalida las demás.',
    'La exportación de traducciones usa la última copia revisada de cada unidad para el idioma actual; no incluye unidades que todavía no tienen traducción. Markdown/DOCX siguen siendo básicos. El ZIP del proyecto conserva también vínculos, encargo y criterios. La IA puede omitir matices: la lectura humana sigue siendo necesaria.'
  ]],
  ['rpg','Mundo para rol: preparación del director',[
    'Mundo para rol es un modo extra. Elegilo en el inicio o en Objetivo para preparar una mesa sin convertirla en un libro. La entrevista pregunta de a una sobre experiencia, tono, límites, sistema o reglas propias y escala del mundo.',
    'Preparar un mundo inicial escribe una petición editable. Enviá cuando quieras. El resultado puede guardarse como material de planificación provisional, sin seleccionar para IA. Marcá las fichas que quieras dar como contexto en los siguientes turnos.',
    'Ficha de historia también ofrece mundo de mesa, PNJ, facción, lugar, reglas del mundo y ganchos. Completá o generá lo que necesites; el director aprueba hechos en Decisiones. Las situaciones quedan abiertas a lo que elijan los jugadores.',
    'La app ayuda a preparar: no dirige partidas ni simula dados, iniciativa o combate. No incluye manuales ni un motor de reglas oficiales de D&D. Si usás un sistema, indicá edición y aportá referencias autorizadas; las reglas inventadas son caseras y provisionales.',
    'Exportar dossier conserva documentos y decisiones en ZIP. Las notas públicas y los secretos del director son secciones del texto, no permisos separados. Revisá el dossier antes de compartirlo con jugadores.'
  ]],
  ['shortcuts','Atajos y navegación',[
    'F1: abrir ayuda. Escape: cerrar el diálogo actual; si hay cambios pendientes, respetá su aviso. Tab y Shift+Tab: recorrer controles. Enter o Espacio: activar un botón o desplegar una explicación.',
    'Ctrl+Enter: enviar desde el mensaje. Ctrl+S: guardar el documento. Ctrl+Z: deshacer. Ctrl+Shift+Z: rehacer. Ctrl+Shift+F: entrar o salir de foco. En macOS se usa Cmd en lugar de Ctrl.',
    'Las explicaciones esenciales también están en esta ayuda y junto a sus controles. Los textos al pasar el puntero son recordatorios opcionales.'
  ]]
];
$('help-topics').innerHTML=helpTopics.map(([id,title,paragraphs])=>`<details id="help-${id}" class="help-topic"><summary>${escapeHTML(title)}</summary>${paragraphs.map(p=>`<p>${escapeHTML(p)}</p>`).join('')}</details>`).join('');
const helpNormalize=text=>text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase();
function filterHelp(){
  const term=helpNormalize($('help-search').value.trim());let count=0;
  for(const topic of $('help-topics').children){topic.hidden=!helpNormalize(topic.textContent).includes(term);if(!topic.hidden)count++;if(term)topic.open=!topic.hidden;}
  $('help-count').textContent=`${count} temas disponibles`;$('help-empty').hidden=count!==0;
}
function openHelp(topic){
  $('help-search').value='';filterHelp();
  for(const detail of $('help-topics').children)detail.open=detail.id==='help-'+topic;
  if(!$('help-dialog').open)showDialog($('help-dialog'));
  const target=helpTopics.some(([id])=>id===topic)?$('help-'+topic):null;
  if(target){target.querySelector('summary').focus();target.scrollIntoView({block:'nearest'});}else $('help-search').focus();
}
$('help-open').onclick=()=>openHelp();$('help-close').onclick=()=>$('help-dialog').close();
$('help-search').oninput=filterHelp;$('help-clear').onclick=()=>{$('help-search').value='';filterHelp();$('help-search').focus();};
document.addEventListener('click',event=>{const button=event.target.closest('[data-help]');if(button){event.preventDefault();openHelp(button.dataset.help);}});
window.addEventListener('keydown',event=>{if(event.key==='F1'){event.preventDefault();openHelp();}});
const tips={
  inspire:'Imagen de fondo del editor. Para claro/oscuro, usá Tema.',
  export:'ZIP de documentos y decisiones guardadas. Para el libro DOCX, usá Plan y avance.',
  'new-thread':'Vacía el chat y reinicia su contexto. Conserva fuentes y decisiones; los chats anteriores se consultan debajo del botón.',
  'new-doc':'Crear un documento de manuscrito vacío en este proyecto.',
  import:'Importar copias Markdown/TXT UTF-8, hasta 250 KB cada una.',
  'template-open':'Crear una ficha provisional; elegís después si compartirla con el asistente.',
  'ai-effort':'Se aplica al próximo mensaje. Más esfuerzo puede tardar más.',
  skill:'Guía editorial local, con alternativa integrada si build-novel no está instalada.',
  download:'Descargar este documento como Markdown, incluido el borrador sin guardar.',
  undo:'Deshacer en este documento. Para versiones guardadas, usá Historial. Ctrl+Z.',
  redo:'Rehacer en este documento. Ctrl+Shift+Z.',
  'auto-read':'Lee las nuevas respuestas con el proveedor de voz autorizado o la voz local de respaldo. Cierra la conversación oral para evitar eco; pulsá el micrófono para retomarla. Se desactiva al cambiar de proyecto.',
  'book-open':'Vista 3D orientativa; no genera una cubierta lista para imprenta.',
  send:'Enviar mensaje al asistente. También Ctrl+Enter desde el mensaje.'
};
for(const [id,text] of Object.entries(tips)){$(id).title=text;const description=document.createElement('span');description.id='tip-'+id;description.className='sr-only';description.textContent=text;document.body.append(description);$(id).setAttribute('aria-describedby',description.id);}
const taskDescriptions={panel:'Lectores simulados e independientes opinan sobre los manuscritos o traducciones marcados. Activá Usar equipo; no reciben canon, sinopsis ni opiniones previas. No modifica el texto.',translate:'Consulta matices antes de traducir. Registrás el criterio y aprobás cada copia por separado.',interview:'Respondé una pregunta por vez. Las ideas siguen siendo provisionales.',draft:'Genera texto para revisar. Solo se guarda como manuscrito cuando elegís hacerlo.',diagnosis:'Señala problemas de las fuentes seleccionadas sin reescribir.',impact:'Explora consecuencias de un cambio hipotético sin aplicarlo.',proposal:'Prepara bloques antes/después para que decidas cuáles aceptar.',chat:'Conversá sobre las fuentes seleccionadas y las decisiones del proyecto.',summary:'Prepara un resumen provisional para retomar; verificá sus fuentes.'};
function updateTaskHelp(){
  $('mode-hint').textContent=state?.purpose==='rpg'&&$('mode').value==='draft'?'Prepara material de rol provisional. El director decide qué conservar.':taskDescriptions[$('mode').value]||'';
  document.querySelector('.task-guidance [data-help]').dataset.help=$('mode').value==='translate'?'translation':state?.purpose==='rpg'?'rpg':['diagnosis','impact','proposal'].includes($('mode').value)?'review':'interview';
}
updateTaskHelp();
$('search-clear').onclick=()=>{$('search').value='';renderDocuments();$('search').focus();};
$('notice-close').onclick=()=>{$('notice').hidden=true;};
function updateLatestAnswer(){$('latest-answer').hidden=!currentRuns().length||$('runs').scrollHeight-$('runs').scrollTop-$('runs').clientHeight<100;}
$('runs').addEventListener('scroll',updateLatestAnswer);$('latest-answer').onclick=()=>{$('runs').scrollTop=$('runs').scrollHeight;updateLatestAnswer();};
$('library-toggle').onclick=()=>{const open=document.body.classList.toggle('library-open');$('library-toggle').setAttribute('aria-expanded',String(open));};
const compactLayout=matchMedia('(max-width:600px)');
function updateLibraryToggle(){$('library-toggle').hidden=!state||state.workflow!=='guided'||!compactLayout.matches;$('library-toggle').setAttribute('aria-expanded',String(document.body.classList.contains('library-open')));}
compactLayout.addEventListener('change',updateLibraryToggle);
