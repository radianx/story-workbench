# Producto

## Problema

Escribir una escena no es lo mismo que sostener un libro. Las decisiones, versiones, voces y hechos del universo deben sobrevivir al cambio de sesión, a las revisiones y a las traducciones. El autor necesita ver qué sabe el asistente y qué está proponiendo cambiar.

## Hipótesis distintiva

«Si cambio esto, ¿qué más debo revisar?» Un cambio de canon produce una propuesta trazable: decisión original, pasajes posiblemente afectados, razón, cambios sugeridos y aprobación por parte del autor. Abarca cuentos, volúmenes y traducciones, sin corregir automáticamente todo el universo.

No se afirma exclusividad comercial ni detección perfecta. La hipótesis debe compararse con herramientas existentes usando tareas iguales. Si otra resuelve satisfactoriamente el problema, evaluar adoptarla o extenderla antes de duplicarla.

## Primera versión útil

1. Abrir una copia local de un libro sin exigir reorganizar sus archivos. Seleccionar explícitamente manuscrito, canon, estilo y material de referencia.
2. Leer y editar Markdown; guardar de forma segura y advertir conflictos con cambios externos.
3. Conversar con Codex desde la interfaz. Mostrar los archivos seleccionados como contexto y distinguirlos de los realmente consultados cuando haya evidencia en los eventos.
4. Pedir una revisión acotada: diagnóstico primero, propuestas después, aceptación o rechazo por bloque. Una propuesta no se convierte en canon por aparecer en el chat.
5. Retomar una sesión con decisiones aprobadas, pendientes y referencias a fuentes. Los resúmenes son derivados y pueden estar desactualizados.
6. Probar una primera revisión de impacto entre dos archivos antes de ampliar a series y traducciones.

## Interfaz

Inspiración de interacción: NotebookLM, no copia de su identidad visual. Biblioteca y fuentes a la izquierda; manuscrito en el centro; asistente, contexto y decisiones a la derecha. Navegación por teclado y controles etiquetados desde el comienzo.

- Inicio de proyecto: wizard con nombre, creación guiada predeterminada y escritura directa opcional, e idea inicial opcional. El modo guiado centra el chat y oculta el material hasta que el autor decida abrirlo. Inicia la entrevista editorial con build-novel local o la guía integrada con una pregunta por turno; funciona sin documentos y permite pasar al editor.
- Voz: dictado español local revisable antes de enviar, lectura local con detención y lectura automática opcional. Micrófono solo mediante acción explícita; audio transitorio y sin transmisión al proveedor en dictado local. La voz online opcional usa OpenAI Realtime o Gemini Live, con clave propia, consentimiento y acciones limitadas.
- Seguimiento: mostrar etapas observadas de cada tarea, respuestas nuevas resaltadas y colapsables. La revisión necesita aceptación explícita; no confundir progreso del turno con progreso de toda la novela.
- Producción: maqueta 3D interactiva con portada, contraportada y lomo; dimensiones físicas ajustables y arte guardado por proyecto. No sustituye la prueba impresa ni exporta una cubierta técnica.
- Distribución: Linux y Windows prioritarios; instaladores que incluyan los runtimes e inicio de sesión ChatGPT desde la interfaz. macOS deseable, fuera del corte actual.
- Apariencia: tema claro, oscuro o del sistema; del sistema por defecto, con elección recordada localmente.
- Normal: paneles de trabajo visibles.
- Foco: oculta paneles secundarios sin cambiar el documento ni detener tareas de manera implícita.
- Inspiración, posterior: imagen opcional por capítulo, generada con consentimiento y reutilizada. Fondo fuera del área de lectura, contraste suficiente y sin animaciones necesarias. Imágenes especulativas no son canon. No prometer disponibilidad ni coste hasta probar la herramienta de generación en esta integración.

## Corte 0.5.0 aplicado

Traducción literaria con encargo/glosario, consultas de matiz, criterio humano, copia revisada separada y exportación por unidades. Modo extra de preparación de mundos para rol, sin juego en vivo. Asistente de voz optativo con OpenAI gpt-realtime o Gemini Live: navegación, mensajes, criterios pendientes y tareas Codex; aprobación editorial siempre manual. En ese corte las claves permanecían solo en memoria y no sustituyen la cuenta ChatGPT del motor editorial. Ver [modos](MODES.md) y [voz, costes y alcance](REALTIME.md).

## Corte 0.4.0 aplicado

Ayuda opcional con búsqueda y accesos contextuales; recordatorios de controles, explicación del tipo de tarea, conservación de mensajes sin enviar por proyecto durante la sesión, errores que se cierran explícitamente y lectura del chat sin saltos. La biblioteca se puede plegar en ventanas compactas guiadas. No hay tour automático ni progreso de tutorial. Ver [revisión de UX](UX_REVIEW.md).

## Corte 0.3.0 aplicado

El recorrido incorpora fichas provisionales, plan de capítulos/escenas, orden editorial, metas de palabras, estados de revisión vinculados a la versión, modelo y esfuerzo elegibles, borrador con guardado explícito y libro compilado en Markdown/DOCX. El plan reutiliza los documentos y comparte sus fichas solo con las fuentes seleccionadas. Ver [evaluación comparativa y propuesta aplicada](PRODUCT_IMPROVEMENTS.md).

## Límites

Primero un autor en su equipo; después pruebas con otros autores usando sus propias cuentas. Sin servicio central que comparta credenciales. Sin generación de libros enteros con un clic, colaboración simultánea ni base vectorial. La versión 0.7.0 amplía la decisión inicial de un único motor: Codex sigue siendo principal y los demás son experimentales. La voz admite dos proveedores explícitos y separados del motor editorial. Exportación editorial avanzada para imprenta/EPUB queda fuera de este corte; la exportación DOCX es básica y no redistribuye build-novel.

Archivos locales no significan inferencia offline: el contexto enviado a Codex sale hacia su servicio. Tampoco eliminan el límite de contexto; seleccionamos material pertinente y explicitamos posibles omisiones.

## Corte 0.6.0 aplicado

Configuración en la barra superior; chat y campo de mensaje amplios, micrófono junto a Enviar, clic para alternar escucha y Espacio mientras se mantiene (solo mensaje vacío). Paletas claras celeste/crema/rosado y oscuras violeta/rojo/azul, además de salvia; modo Sistema inicial y una sola lista de temas en Configuración y en el primer paso del asistente inicial. Ayuda y voz con modales adaptables, estado de cuenta accesible con punto de color, giro del libro por mouse/teclado. Acepta claves Gemini auth AQ. y permite recordar claves cifradas en el almacén nativo de escritorio; nunca en proyectos ni localStorage.

## Corte 0.6.1 aplicado

Apariencia persistida antes del primer pintado y verificación entre arranques de Electron. Microinteracciones ligadas a estados: espera de acciones, guardado, final de tarea, apertura de diálogos, micrófono y controles 3D. Movimiento reducido del sistema desactiva animaciones conservando feedback textual y funcional. Ver [pasada de UX](UX_REVIEW.md).

## Corte 0.7.0 aplicado

Asistente de primera apertura: cuenta, voz opcional y proyecto; omisible, persistente y reabrible. Navegador de secciones con Ctrl/Cmd+K, Ctrl/Cmd+, para configuración, flechas en pestañas y destinos compartidos con voz. Claves, permisos y aprobaciones requieren acción humana; no se afirma operación 100% por voz desde una instalación vacía.

Maqueta de tapa blanda con tamaño inicial 6 × 9 pulgadas, estimación de páginas desde manuscritos guardados según área útil, páginas reales o lomo manual. Papel blanco/crema; valores anteriores permanecen manuales. No es paginación definitiva ni archivo de imprenta.

Codex/ChatGPT principal y seis adaptadores editoriales experimentales: OpenAI API, Gemini, Anthropic, DeepSeek, Kimi y servidor local. Selección explícita por proyecto, claves propias cifrables, sin fallback. Ver [alcance y fuentes](PROVIDERS.md).

## Lectura online en Tauri 0.8.0

Escuchar respuestas usa el proveedor de voz autorizado, OpenAI Realtime o Gemini Live, con TTS local como respaldo automático. La preferencia Siempre voz local queda guardada. Volumen de voz (0–100%) se recuerda para el usuario y controla conversación online y lectura sin cambiar el micrófono. La lectura no abre el micrófono, no dispone de herramientas y no recibe contexto editorial adicional al texto que el autor eligió escuchar. La lectura automática se activa con Leer respuestas junto al micrófono; desmarcarla detiene la lectura y cambiar de proyecto la desactiva. Usa WebSocket y no requiere WebRTC; la conversación oral OpenAI sigue teniendo esa limitación en el WebKit de este Linux. Ver [lectura y comprobaciones](REALTIME.md#lectura-de-respuestas). Incluida en la distribución Tauri 0.8.0.

## Escritorio Tauri 0.8.0

Tauri reemplaza Electron como único shell. Paquetes locales .deb y NSIS; Python, Codex y modelo de voz incluidos. Reutiliza la carpeta de proyectos y sesión Codex anterior. El perfil web y llavero nativo son nuevos: preferencias y claves antiguas requieren configuración una vez. Exportaciones con diálogo Guardar y escritura atómica; cierre cancelable con texto sin guardar o tarea activa. Estado ejecutado y limitaciones por plataforma en [distribución](DESKTOP.md).

## Inicio de traducción y carpetas

El proyecto de traducción nuevo requiere material previo e idiomas elegidos por el autor, con sugerencia local de idioma original. No pide inventar una historia. El wizard divide el original en unidades reversibles y abre la entrevista con el encargo preparado. Importación de carpetas con selección de Markdown/TXT y copias independientes; espacio de proyectos elegible o creable en Configuración, persistido y aplicado al reiniciar sin mover obras ni cuentas.


## Corte 0.8.4 aplicado

Archivo reversible de proyectos, prueba explícita del proveedor de voz sin TTS de respaldo, Neón y Vice City claros/oscuros, paletas personalizadas JSON y opacidad persistente. Modelo y esfuerzo Codex aparecen junto al tipo de tarea del chat; los adaptadores experimentales conservan su configuración propia. Ver [temas](THEMES.md).

## Corte 0.8.5: equipo editorial y conversaciones

Equipo experimental optativo por mensaje, solo con Codex/ChatGPT y fuera de la entrevista. Configuración por proyecto: modelo y esfuerzo explícitos de los colaboradores, máximo de uno a tres y perfiles del panel. Incluye selecciones rápidas Luna máximo y Sol bajo/medio, si están disponibles en el catálogo de la cuenta; nunca se sustituye un modelo automáticamente. El principal conserva los controles del chat.

La app coordina sesiones App Server independientes con permisos restringidos. El principal reparte tareas acotadas dentro del pedido y las fuentes seleccionadas; los colaboradores devuelven aportes provisionales y el principal los integra. No delegan recursivamente. La casilla Usar equipo muestra el máximo de turnos y advierte que puede consumir bastante más cuota; modelos livianos no garantizan ahorro. Una tarea global a la vez: reparto y colaboradores hasta seis minutos, síntesis hasta cuatro. Detener cierra todos los colaboradores; un fallo conserva los aportes completados sin presentarlos como resultado final.

Panel ciego inspirado en el flujo build-novel: perfiles de lector impaciente, voz/estilo, personajes/emoción y causalidad/pistas, hasta tres elegidos. Cada uno comienza una sesión nueva y recibe únicamente los manuscritos/traducciones seleccionados en orden y su consigna neutral; sin sinopsis, canon, intención del autor, conversación ni otros informes. El principal sintetiza coincidencias, desacuerdos y preguntas al autor; no decide por mayoría. Son lectores simulados, no lectores humanos ni predictores de ventas. No se redistribuye la skill global.

[Codex documenta](https://learn.chatgpt.com/docs/agent-configuration/subagents) que los subagentes aumentan el consumo y que las opciones explícitas de creación prevalecen sobre sus valores predeterminados. Por eso la app fija el modelo de cada sesión colaboradora y conserva deshabilitada la delegación nativa libre. Los adaptadores editoriales experimentales siguen con un único agente. No hay generación automática de un libro entero ni aprobación de canon por el equipo.

Nueva conversación vacía el chat actual y reinicia el historial que reciben Codex, los adaptadores y la voz. Conserva fuentes, decisiones y propuestas del proyecto. Los chats previos quedan en un desplegable debajo del botón, consultables sin volver a enviarlos a la IA; también se conserva un mensaje que haya quedado sin enviar. Abrir ese historial o recargar un chat nuevo no inicia una tarea. Los historiales de versiones anteriores se conservan agrupados.

Ver material usa la paleta activa en sus controles, bordes y pie, también para temas personalizados. El selector de tema ocupa todo el ancho disponible en Apariencia e inicio.

Tipografía de la app elegible entre cinco familias web safe, en el mismo panel de apariencia y en el inicio: Sistema/sans-serif, Arial/Liberation Sans, Georgia/serif, Times New Roman/Liberation Serif y Courier New/Liberation Mono. Se recuerda por usuario, se aplica antes del primer pintado y no descarga fuentes ni modifica los manuscritos.


## Salida de voz 0.8.6

En WebKit de Linux, Gemini y la lectura online reproducen cada turno como WAV en memoria para evitar la salida PCM intermitente observada con Web Audio. Espera el final de cada turno; mantiene volumen, detención, interrupciones y hasta 90 segundos pendientes. Los demás motores conservan streaming. Ver [comprobaciones de señal y límites](MVP_RESULTS.md) y [voz](REALTIME.md).

## Reproducción incremental 0.8.7

La salida multimedia de Linux comienza con los primeros bloques PCM y precarga los siguientes durante la reproducción. Reemplaza la espera del turno completo introducida en 0.8.6; comparte el cambio entre conversación Gemini y lectura online. Conserva el control de volumen, interrupción y límite de memoria. La conexión y el primer audio dependen del proveedor. Ver [mediciones ejecutadas](MVP_RESULTS.md).

## Voz integrada al chat 0.8.8

La opción predeterminada de voz conecta el audio con el chat editorial: transcribe y envía mediante el mismo flujo del teclado, luego lee la respuesta del motor elegido. Conserva la conexión oral con el micrófono pausado durante tarea y lectura, respeta borradores y permite desactivar el envío o la lectura. El asistente oral con herramientas sigue disponible bajo Controles de la app. Ver [voz](REALTIME.md).

## Lectura fiel al chat 0.8.9

Se corrigió el uso de modelos conversacionales para leer: Gemini Live podía contestar las preguntas del chat aunque recibiera instrucciones de recitarlas. El audio de salida ahora usa Gemini 3.1 Flash TTS Preview o gpt-4o-mini-tts, con la misma clave del proveedor. Conserva audio incremental, volumen, cancelación, micrófono pausado y voz local de respaldo. Live/Realtime sigue transcribiendo la entrada. Las comprobaciones comparan también el contenido audible de preguntas, opciones y una orden citada.

## Chat 0.8.10

Enter envía y Shift+Enter inserta un salto de línea. Enviar, el micrófono y Leer respuestas acompañan al campo de texto; tarea/modelo/esfuerzo usan una fila inferior desplazable en espacios estrechos. El chat baja al final ante mensajes nuevos y texto entrante del agente. Las respuestas, su historial y los aportes del equipo muestran Markdown: encabezados, énfasis, listas, citas, código, enlaces y tablas con desplazamiento horizontal. La vista previa comparte el parser; el texto guardado conserva su formato original. HTML se muestra como texto y las imágenes no se descargan automáticamente.

## Avisos y envío 0.8.11

Enviar es más grande y muestra ↵; Leer respuestas queda debajo. La pestaña Avisos reúne hasta 100 notificaciones de esta ventana, agrupa repeticiones consecutivas y marca como leídos al abrirla, sin tapar ni cambiar el chat. Incluye Limpiar avisos y acceso mediante la navegación de teclado/voz. No guarda notificaciones en disco. Los formularios conservan sus mensajes dentro del diálogo y el inicio sin proyecto los muestra en su contenido.

## Tarjetas en Avisos 0.8.12

Avisos contiene también la orientación de traducción o rol y el progreso de la tarea actual. Conserva sus acciones y actualiza las etapas aunque se esté leyendo la conversación; estas tarjetas no se borran al limpiar las notificaciones. El chat queda libre de esas tarjetas.

## Corte 0.9.0

Importación de obras EPUB sin DRM y DOCX como copias de texto, en el wizard y la biblioteca. Exportación PDF de lectura con páginas y dimensiones configuradas. Imágenes mediante APIs OpenAI/Gemini experimentales: configuración propia visible, consentimiento por generación, vista previa, guardado explícito y descarga del original; reutilización opcional como portada 3D. Codex con ChatGPT sigue siendo el motor editorial principal. No se ha conectado la generación de imágenes de Codex a este flujo.

Backend reorganizado en `src/`, operaciones separadas de HTTP, metadatos versionados y primeros módulos ES del frontend. Ninguno de estos cambios modifica repositorios de obras originales.

## Adjuntos visuales de Codex (posterior a 0.9.0)

La generación nativa de imágenes de Codex queda conectada al chat individual de entrevista, conversación y borrador. El pedido debe ser explícito; usa la sesión ChatGPT y conserva las restricciones de los demás trabajos. Los resultados PNG/JPEG se guardan como adjuntos provisionales, con miniatura, visor con zoom y descarga del original, también en el historial y la galería. No aprueban canon ni sustituyen una portada. La pantalla de APIs de imágenes continúa como alternativa experimental con clave propia.
