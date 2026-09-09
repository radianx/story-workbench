'use strict';
// Ayuda propia, incluida con la app: no carga páginas externas ni llama al asistente.
const helpTopics = [
  ['interview','Empezar y continuar la entrevista',[
    'Elegí Crear mi proyecto y Crear conversando. Una idea incompleta alcanza: el agente pregunta de a una. Si falta conectar ChatGPT, la app te muestra el acceso a tu cuenta.',
    'Respondé en el mensaje o usá Dictar respuesta. Enviar inicia el trabajo y consume tu cuota de Codex. Podés detener una tarea sin convertir su respuesta en material aprobado.',
    'Cuando quieras avanzar, cambiá Tipo de tarea a Redactar borrador. Guardar como borrador provisional crea un documento nuevo únicamente cuando lo elegís. Ver material abre el editor; Ocultar material devuelve espacio al chat.',
    'Nueva conversación inicia otro hilo al enviar el próximo mensaje. Las conversaciones anteriores y las decisiones siguen guardadas. La forma de trabajo se puede cambiar desde Biblioteca.'
  ]],
  ['sources','Fuentes, biblioteca y fichas',[
    'Las casillas junto a los documentos eligen qué texto recibe el asistente. Abrir un documento para leerlo no lo selecciona para IA. Para hablar de una fuente, marcala y guardá sus cambios primero.',
    'Cambiar la selección abre un hilo nuevo en el próximo envío para retirar el contexto anterior. La idea inicial y las decisiones del proyecto también se envían. Máximo: 60.000 caracteres de fuentes y sus fichas del plan; no se recortan en silencio.',
    'Importar copias admite Markdown y TXT en UTF-8, hasta 250 KB por archivo. Los originales permanecen en su lugar. Los archivos importados quedan seleccionados; revisá las casillas antes de enviar.',
    'Ficha de historia crea una plantilla de personaje, mundo, voz o arco. Empieza como documento provisional sin seleccionar para IA. Completala y seleccioná su casilla cuando quieras compartirla.',
    'Tipos: Manuscrito forma el libro exportado; Canon contiene hechos establecidos por vos; Voz y estilo orienta la prosa; Planificación organiza ideas; Referencia aporta material de apoyo; Traducción conserva otro idioma. El tipo no aprueba automáticamente el contenido.'
  ]],
  ['models','Cuenta, modelo y esfuerzo',[
    'Cuenta ChatGPT abre el inicio de sesión en tu navegador. Cada autor usa su propia cuenta. La escritura local funciona sin iniciar sesión; el asistente necesita internet y cuota disponible. No hay claves API ni fallback de pago.',
    'Desplegá Modelo y esfuerzo junto al mensaje para elegirlos. Se guardan por proyecto y se aplican al próximo mensaje. Solo aparecen opciones compatibles que devuelve tu cuenta. Actualizar modelos vuelve a consultar su disponibilidad.',
    'Un esfuerzo mayor puede tardar más; no garantiza mejor voz literaria. Si un modelo guardado deja de estar disponible, elegí otro. La app no lo sustituye en silencio.',
    'La guía editorial usa build-novel si está instalada, o la guía integrada cuando no está disponible. No necesitás instalar una skill para empezar.'
  ]],
  ['voice','Dictado, micrófono y lectura en voz alta',[
    'Dictar respuesta activa el micrófono al pulsarlo. Terminá el dictado o descartalo; cada captura admite hasta 45 segundos. La transcripción aparece en el mensaje para corregirla antes de Enviar. Los nombres propios pueden necesitar correcciones.',
    'El audio se procesa localmente en español, permanece solo en memoria y no se envía a ChatGPT. El micrófono se apaga al terminar, descartar o cambiar de proyecto. Enviar comparte el texto del mensaje con el asistente.',
    'Escuchar lee una respuesta con la voz del sistema. Detener lectura la interrumpe. Leer respuestas nuevas es opcional y se desactiva al cambiar de proyecto; no reproduce todo el historial.',
    'Si no funciona el micrófono, revisá el permiso de la app o navegador y el dispositivo de entrada del sistema. Si indica que falta el motor, usá el instalador con voz. Si falta lectura, revisá las voces instaladas de Windows o la instalación del paquete Linux. Siempre podés responder por escrito.'
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
    'Tema controla Claro, Oscuro o Sistema; Sistema es el valor inicial. Ambiente es otra cosa: una imagen tenue detrás del editor, local a esta pestaña. No se envía al asistente y se retira al cambiar de proyecto.',
    'Modo foco oculta paneles secundarios. En creación guiada prioriza el chat; en escritura prioriza el documento. Salir de foco recupera los paneles sin detener una tarea.',
    'Libro 3D es una maqueta visual de portada, lomo, contraportada y páginas. Usá las medidas y el grosor que confirme tu imprenta. El lomo no se calcula a partir del contador de palabras.',
    'Guardar maqueta conserva medidas y copias de las imágenes en el proyecto. Girar el libro solo cambia la vista. La maqueta no es una cubierta técnica lista para imprimir.'
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
  if(!$('help-dialog').open)$('help-dialog').showModal();
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
  'new-thread':'El próximo mensaje abre otro hilo; conserva el historial anterior y las decisiones.',
  'new-doc':'Crear un documento de manuscrito vacío en este proyecto.',
  import:'Importar copias Markdown/TXT UTF-8, hasta 250 KB cada una.',
  'template-open':'Crear una ficha provisional; elegís después si compartirla con el asistente.',
  'ai-effort':'Se aplica al próximo mensaje. Más esfuerzo puede tardar más.',
  skill:'Guía editorial local, con alternativa integrada si build-novel no está instalada.',
  download:'Descargar este documento como Markdown, incluido el borrador sin guardar.',
  undo:'Deshacer en este documento. Para versiones guardadas, usá Historial. Ctrl+Z.',
  redo:'Rehacer en este documento. Ctrl+Shift+Z.',
  'auto-read':'Leer solo las respuestas nuevas. Se desactiva al cambiar de proyecto.',
  'book-open':'Vista 3D orientativa; no genera una cubierta lista para imprenta.',
  send:'Enviar mensaje al asistente. También Ctrl+Enter desde el mensaje.'
};
for(const [id,text] of Object.entries(tips)){$(id).title=text;const description=document.createElement('span');description.id='tip-'+id;description.className='sr-only';description.textContent=text;document.body.append(description);$(id).setAttribute('aria-describedby',description.id);}
const taskDescriptions={interview:'Respondé una pregunta por vez. Las ideas siguen siendo provisionales.',draft:'Genera texto para revisar. Solo se guarda como manuscrito cuando elegís hacerlo.',diagnosis:'Señala problemas de las fuentes seleccionadas sin reescribir.',impact:'Explora consecuencias de un cambio hipotético sin aplicarlo.',proposal:'Prepara bloques antes/después para que decidas cuáles aceptar.',chat:'Conversá sobre las fuentes seleccionadas y las decisiones del proyecto.',summary:'Prepara un resumen provisional para retomar; verificá sus fuentes.'};
function updateTaskHelp(){
  $('mode-hint').textContent=taskDescriptions[$('mode').value]||'';
  document.querySelector('.task-guidance [data-help]').dataset.help=['diagnosis','impact','proposal'].includes($('mode').value)?'review':'interview';
}
updateTaskHelp();
$('search-clear').onclick=()=>{$('search').value='';renderDocuments();$('search').focus();};
$('notice-close').onclick=()=>{$('notice').hidden=true;};
function updateLatestAnswer(){$('latest-answer').hidden=!state?.runs.length||$('runs').scrollHeight-$('runs').scrollTop-$('runs').clientHeight<100;}
$('runs').addEventListener('scroll',updateLatestAnswer);$('latest-answer').onclick=()=>{$('runs').scrollTop=$('runs').scrollHeight;updateLatestAnswer();};
$('library-toggle').onclick=()=>{const open=document.body.classList.toggle('library-open');$('library-toggle').setAttribute('aria-expanded',String(open));};
const compactLayout=matchMedia('(max-width:600px)');
function updateLibraryToggle(){$('library-toggle').hidden=!state||state.workflow!=='guided'||!compactLayout.matches;$('library-toggle').setAttribute('aria-expanded',String(document.body.classList.contains('library-open')));}
compactLayout.addEventListener('change',updateLibraryToggle);
