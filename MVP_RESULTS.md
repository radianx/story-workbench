# Avisos y controles de envío · Tauri 0.8.11 — 2026-09-10

- Enviar ampliado a un mínimo de 132 × 52 px, símbolo ↵ decorativo y casilla Leer respuestas debajo. Conserva Enter/Shift+Enter y el micrófono junto al campo.
- Avisos sustituye los mensajes flotantes durante el trabajo: contador de nuevos, marcado al consultar, limpieza, hora y proyecto, repeticiones consecutivas agrupadas. Hasta 100 entradas en memoria de la ventana; no se guardan en disco. Los formularios y el inicio sin proyecto conservan feedback dentro de su contenido.
- Pasaron los recorridos UX, setup, microinteracciones y temas/archivo con ficción. Se comprobaron disposición/tamaño de Enviar, atajos, scroll, contador, agrupación, límite de 100, texto HTML inerte, navegación compartida con voz, limpieza sin escrituras y errores visibles en diálogos anidados tanto en escritorio como en ventana compacta. Sin llamadas IA ni micrófono físico.
- Instaladores Tauri 0.8.11 Linux .deb y Windows NSIS generados. Verificados 32/103 archivos de runtime, fuentes Windows y SHA256 de ambos paquetes. No se probó interfaz Windows real ni se actualizó la instalación del usuario.

# Chat, formato y teclado · Tauri 0.8.10 — 2026-09-10

- Enter envía desde el mensaje y Shift+Enter inserta un salto de línea. Conserva Ctrl/Cmd+Enter y reutiliza el botón Enviar, incluidos sus bloqueos. La repetición de tecla y la confirmación de composición IME no envían mensajes.
- Pasó `tests/ux_browser_check.py` con envíos simulados: Enter, texto multilínea, Ctrl+Enter, composición IME, tecla repetida, botón deshabilitado, mensaje vacío y conservación de texto escrito durante el envío. También pasó la comprobación de sintaxis JavaScript. Sin llamadas IA ni micrófono.
- Enviar, micrófono y Leer respuestas comparten altura con el texto en escritorio; tarea/modelo/esfuerzo comparten una fila inferior. La comprobación midió sus posiciones y verificó vista compacta. Los controles inferiores se desplazan horizontalmente cuando falta espacio. El chat baja al final ante mensajes o texto del agente nuevos; comprobado incluso desde una posición de lectura anterior.
- `tests/markdown_browser_check.py` pasó con Markdown incremental y completo: encabezados, énfasis, tachado, listas anidadas, citas, código literal y tablas alineadas/desplazables en chat, historial, equipo y vista previa. Verificó que HTML queda inerte, enlaces ejecutables/locales no se activan, imágenes no se descargan y el texto original persiste. Parser markdown-it local, con licencias incluidas.
- Pasaron 45 pruebas Python y cuatro pruebas Rust, incluida la validación de enlaces HTTP/HTTPS al navegador externo. No se abrieron enlaces externos durante estas comprobaciones.
- Pasaron las regresiones de dictado/lectura locales, lector online simulado con la cola multimedia Linux y voz → chat → lector. Instaladores 0.8.10 Linux .deb y Windows NSIS generados; 32/103 archivos de runtime, fuentes Windows y SHA256 verificados. No se probó interfaz Windows real ni se actualizó la instalación del usuario.

# Lectura TTS del texto editorial · Tauri 0.8.9 — 2026-09-10

- Reproducido con Gemini Live real: ante «¿Qué pierde la protagonista si decide volver?» el audio respondió que faltaba el texto de la historia. La validación de 0.8.8 había comprobado entrega de audio, sin contrastar lo dicho; no probaba fidelidad al chat.
- Sustituida la lectura conversacional por Gemini 3.1 Flash TTS Preview (Kore) y gpt-4o-mini-tts (Marin). Misma clave del proveedor, modelos indicados en Configuración. Gemini usa SSE y OpenAI PCM HTTP; el backend entrega bloques al reproductor existente, sin esperar el audio completo. Live/Realtime conserva la entrada de voz.
- Tres pruebas Gemini reales desde el lector de la app en Chrome, sin micrófono ni manuscritos: pregunta, elección entre personas narrativas y una orden citada. Se reconstruyó el PCM recibido y se transcribió con Vosk local. Duraciones 3,24 / 8,12 / 8,48 s; las salidas conservaron el contenido en vez de responder. El reconocedor confundió «protagonista si» con «protagonistas y» en una muestra; las otras dos coincidieron al ignorar puntuación. No constituye garantía absoluta de pronunciación.
- La comprobación ejecutable de fidelidad pasó sobre esos tres WAV reales, sin nuevas llamadas API: 97 / 100 / 100 % de similitud de caracteres normalizados. La primera comparación por palabras daba un falso rechazo ante «protagonistas y»; se ajustó la métrica y se comprobó que sigue rechazando la respuesta libre de Live. La repetición completa del script contra API no terminó antes de ese ajuste; la validación final reutilizó los tres audios capturados desde la app.
- Una sonda inicial del endpoint recibió el primer PCM a los 1,66 s; un ensayo posterior a los 1,70 s. Son tiempos de esas peticiones, no garantías de latencia. Una repetición encontró un error del proveedor: se informa acceso/cuota/transporte y se conserva el respaldo local.
- Pasaron 45 pruebas de backend, lectura simulada en Web Audio y ruta multimedia Linux, y el flujo voz → chat → lector con pausa/reanudación. Contrato de texto íntegro, endpoints no conversacionales, límites, formato, cancelación y errores sin secretos incluidos. OpenAI TTS se verificó con transporte simulado, sin API real.
- Instaladores Tauri 0.8.9 Linux .deb y Windows NSIS generados; verificados 32/100 archivos de runtime, fuentes Windows y SHA256. No se repitió el recorrido nativo completo de Tauri ni se verificó la interfaz en Windows real. No se instaló esta versión sobre la aplicación del usuario.

# Voz integrada al chat · Tauri 0.8.8 — 2026-09-10

- Voz del chat predeterminada y persistente: transcripción enviada por el mismo flujo que el teclado, lectura de la respuesta del motor editorial y pausa del micrófono durante tarea/lectura. Controles de la app conserva las herramientas en un modo explícitamente separado. Gemini no decide qué enviar ni responde por su cuenta en Voz del chat.
- `tests/voice_chat_browser_check.py` comprobó envío persistente único, fragmentos de transcripción posteriores al fin de turno, lectura del resultado editorial, reanudación de micrófono, conservación de borrador previo, permisos, cancelación y deduplicación OpenAI. Servicios simulados y micrófono virtual.
- Prueba real Gemini mediante Chrome con una grabación ficticia como micrófono virtual: audio → transcripción → mensaje guardado → respuesta editorial simulada → audio lector Gemini. Clave existente en memoria, sin manuscritos ni micrófono físico. No ejecutó una tarea Codex real. Una sonda Python WebSocket anterior perdió la conexión; el recorrido posterior del navegador completó el puente.
- Instaladores 0.8.8 Linux .deb y Windows NSIS generados, con 32/100 archivos y SHA256 verificados. El equipo mantiene instalada 0.8.7; requiere actualizar y reiniciar. No se probó interfaz Windows real ni una nueva tarea Codex real.
- Pasaron las 45 pruebas de backend, incluida la configuración de transcripción sin herramientas ni contexto editorial.
- Pasaron regresiones de controles Gemini y OpenAI, y lectura con la cola multimedia Linux. La entrada OpenAI se comprobó con servicios simulados; conserva el límite WebRTC del WebKitGTK local.

# Reproducción incremental · Tauri 0.8.7 — 2026-09-10

- El usuario confirmó que 0.8.6 ya se escucha en la app. Para reducir su espera, Linux empieza con un bloque WAV corto y precarga los siguientes; ya no espera el turno completo. Conversación Gemini y lectura online comparten la cola, sin cambiar el formato de entrada del micrófono ni Web Audio en otros motores.
- `node tests/pcm_playback_check.js` pasó: inicio por cantidad y por temporizador, precarga, secuencia de muestras WAV, volumen actualizado, cancelación de temporizador y cola, errores y límite de memoria.
- `tests/webkit_audio_stream_check.py` ejecutó WebKitGTK real con 60 paquetes PCM ficticios, salida Pulse virtual propia y captura de esa salida. Con paquetes cada 60/100 ms, el primer inicio ocurrió a los 622/663 ms desde el primer paquete; se recuperaron 6,03/5,97 segundos de señal. A resolución de 10 ms, se detectaron cero pausas en el primer caso y una de 10 ms en el segundo. No usa micrófono, API ni audio de otras aplicaciones y elimina la salida temporal.
- El automatizador espera a que la página termine de cargar, como ocurre antes de iniciar voz en la app. Una versión del ensayo que emitía durante el análisis inicial del HTML produjo avisos de reproducción tardíos; esos resultados no se usaron como medida de latencia del flujo normal.
- Pasaron los cuatro recorridos de navegador: lectura y conversación Gemini, tanto con Web Audio como con la cola multimedia de Linux. Proveedores simulados; volumen, interrupción, detención y TTS de respaldo comprobados.
- Instaladores 0.8.7 Linux .deb y Windows NSIS generados; 32/100 archivos verificados contra manifiestos y SHA256. La interfaz Windows real no se comprobó. El equipo conserva instalado 0.8.6; actualizar requiere el instalador y la autenticación administrativa habitual.
- Estas medidas excluyen conexión y generación del primer audio del proveedor; no garantizan latencia ante cortes de red ni equivalen a una nueva escucha física por el usuario.

# Salida de voz en Linux · Tauri 0.8.6 — 2026-09-10

- Reproducido el fallo sin Gemini: tonos PCM enviados por Web Audio en WebKitGTK 2.52.6 perdían señal o llegaban alterados. Cambiar frecuencia, retrasar el cierre o habilitar el mezclador no estabilizó la salida. Los WAV por el reproductor multimedia sí dieron señal uniforme.
- WebKit de Linux reúne la respuesta PCM por turno y reproduce un WAV en memoria, compartido por Gemini conversacional y la lectura Gemini/OpenAI. Conserva volumen, cola, cancelación y errores; espera el final del turno y limita a 90 segundos el audio pendiente. No modifica el formato del micrófono ni cambia el streaming de otros motores.
- Pasaron 44 pruebas de backend, cinco recorridos de navegador (lectura y conversación Gemini en ambas rutas, más voz local), y la comprobación Node de cabecera/contenido WAV, orden, volumen, cancelación, error y límite de memoria.
- `tests/webkit_audio_output_check.py` midió cuatro tonos completos de tres segundos, sin huecos y con RMS estable, dirigidos a HAYLOU S35 ANC; dos con el reloj de entrada de 16 kHz activo, sin micrófono. La captura se limita al flujo de la prueba.
- Tres pruebas reales desde Configuración de la app extraída, con la clave ya guardada y una frase ficticia: respuestas de 5,9 / 5,8 / 6,5 segundos, con señal de voz medida en la salida Bluetooth. En la tercera, el pico capturado fue 26895/32768. No se usó TTS de respaldo ni se abrió el micrófono. Esto verifica entrega al sistema de audio; la escucha física sostenida por el usuario queda por confirmar.
- Se restableció al 100% el flujo de reproducción atenuado por el volumen recordado del sistema. Las pruebas nativas comparten los roles de audio de la sesión: un identificador de aplicación separado no aísla ese volumen en este PipeWire. No se dejó aplicado ese intento de aislamiento ni se cambió el perfil Bluetooth.
- El paquete final pasó dos arranques Tauri con perfil y claves ficticios. Se corrigió una carrera del automatizador: espera `DOMContentLoaded` antes de utilizar los scripts diferidos. Verificados instaladores Linux .deb y Windows NSIS, 32/100 archivos de runtime e integridad SHA256. No se validó interfaz Windows real.
- La versión extraída quedó abierta para prueba local. La instalación del .deb requiere contraseña de administrador; no se reemplazó el paquete instalado. Sin cambios en manuscritos ni credenciales en el repositorio.

# Equipo editorial, chats y apariencia · Tauri 0.8.5 — 2026-09-10

- Pasaron 44 pruebas de backend y 4 de Rust. Equipo limitado a tres colaboradores con modelo/esfuerzo explícitos, validación antes de inferencia, reparto con fuentes permitidas, rechazo de modelo inesperado antes de enviar una tarea, cancelación conjunta y recuperación del estado de tareas interrumpidas al reiniciar. El panel excluye del contexto de cada lector sinopsis, canon, intención, conversaciones y opiniones ajenas; comparación de Markdown antes/después sin cambios.
- Dos comprobaciones reales con ficción temporal y sesión ChatGPT: panel con dos Luna/max y síntesis Sol/low; diagnóstico con reparto Sol/low, un Luna/max y síntesis Sol/low. Se completaron las tareas y no se guardaron reescrituras ni propuestas. No se usaron APIs de pago. Esto valida el recorrido, no cuantifica ahorro de cuota ni calidad editorial general.
- Pasaron once recorridos Chrome: editor, configuración, motores, modos, voz, Realtime, lectura, setup, movimiento, temas/archivo y equipo/chats. Servicios de voz simulados. Nueva conversación vacía la ventana y los contextos editorial/voz, conserva archivos, decisiones y borrador sin enviar, archiva historial consultable y no inicia un turno al recargar en modo guiado.
- Tipografías Sistema, Arial/Liberation Sans, Georgia, Times New Roman/Liberation Serif y Courier New/Liberation Mono: selección inmediata, persistencia previa al pintado, coherencia entre interfaz/chat/material y fallback ante preferencia inválida. Sin descargas de fuentes. Selector de tema de ancho completo y colores del material vinculados a la paleta, comprobados también con tema personalizado y a 390 px.
- La regresión de voz detectó que la fila de modelo/esfuerzo podía invadir el micrófono en una columna estrecha. Se corrigió la base flex de esa fila; los recorridos de dictado y lectura pasaron al repetirlos.

- El .deb final pasó dos arranques nativos Tauri/WebKitGTK, seis exportaciones y cuatro selectores de carpeta, con Xvfb, bus D-Bus y Secret Service temporales. Tipografía, tema y volumen persistieron; las claves ficticias se guardaron, recuperaron y borraron. Voz con dispositivos virtuales y proveedores simulados. WebRTC sigue sin estar disponible en este WebKit.
- El ensayo detectó un problema de su corpus: dejaba un proyecto guiado sin entrevista, que al reiniciar abría correctamente el diálogo de cuenta. El automatizador intentaba navegar sin cerrarlo. Se cambió ese proyecto de prueba a escritura y se agregó el mensaje de error al diagnóstico. Otro intento encontró el llavero del usuario no disponible; la comprobación final usó un llavero temporal aislado. No se debilitó la protección de diálogos ni el acceso a claves.
- Instaladores locales .deb y NSIS generados; 32 archivos Linux y 100 Windows verificados contra manifiestos y SHA256. El backend Windows completó dos arranques bajo Wine, validó el módulo de equipo sin catálogo/cuenta, sirvió su interfaz y liberó el puerto y bloqueo al cerrar stdin. Instalación e interfaz Windows nativas pendientes; paquetes sin firma ni publicación.
- `Story-Workbench-0.8.5-linux-amd64.deb`: 193034316 bytes; SHA256 `eb8b03b1f4b3cfac0d02aaf89e76b6fbcbbad2aca258d49a97069ac85b5b3b72`.
- `Story-Workbench-0.8.5-win-x64.exe`: 208574302 bytes; SHA256 `140760adbc1ab0d65422af1b0c2452677f032bc2f97d32ce4e055644a578b49b`.

# Personalización, archivo y prueba de voz · Tauri 0.8.4 — 2026-09-10

- Pasaron 39 pruebas de backend y 4 de Rust. Archivo/restauración persistente, rechazo de tareas activas y estados inválidos, y recuperación de tareas interrumpidas incluso en proyectos ocultos. Comparación de archivos antes/después: ningún documento o historial eliminado.
- Pasaron los recorridos Chrome de editor, configuración, motores, setup, UX, Gemini, lectura y temas/archivo. Modelo y esfuerzo conservan compatibilidad y persistencia desde el chat; los adaptadores siguen separados. Diseño comprobado en 1920 px y 390 px.
- Neón y Vice City claros/oscuros; crear, editar, exportar e importar paletas JSON, rechazar colores/URLs inválidos antes de guardar, recuperar preferencias al recargar y recordar la opacidad. La imagen de ambiente conserva su duración por sesión/proyecto.
- La prueba de voz usa una frase ficticia y no llama al TTS de respaldo. Probados respuesta PCM, ausencia de audio, silencio, error, cancelación, volumen cero y falta de consentimiento. Se verificó que no abre el micrófono ni registra tareas editoriales. No se llamó a Gemini/OpenAI reales en este corte; la escucha real de Gemini sigue por confirmar.
- El paquete Linux pasó dos arranques Tauri/WebKit en Xvfb: tema personalizado y opacidad recordados, modelo en el chat, prueba de voz simulada, llavero nativo con claves ficticias, seis exportaciones y cuatro selectores de carpeta. Se corrigió el automatizador GTK para conservar la misma acción cuando Escape no cierra el diálogo; el primer intento había contado ese reintento como una exportación nueva.
- Generados instaladores 0.8.4 Linux .deb y Windows NSIS. Verificados 32/98 archivos de runtime, correspondencia de fuentes Windows y hashes SHA256. El backend Windows pasó bajo Wine: handshake, HTTP, cierre por stdin y segundo arranque. No se verificaron instalación ni interfaz en Windows real.
- Los subagentes se evaluaron y documentaron como propuesta en PRODUCT.md; no se habilitaron ni se modificaron límites editoriales o de archivos.

# Traducción desde una obra y carpetas · Tauri 0.8.3 — 2026-09-09

- Pasaron las 37 pruebas de backend y los recorridos Chrome de modos, setup y editor. La traducción nueva exige original e idiomas; el encargo llega preparado a la entrevista, con sugerencia local corregible y sin idea inicial. Se comprueba detección de seis idiomas, abstención en textos breves/ambiguos y partición de originales largos sin omisiones.
- La importación de carpeta permite seleccionar Markdown/TXT, mantiene nombres relativos y deja las copias sin seleccionar para IA (excepto la primera unidad de traducción). Rechaza recorridos de rutas, enlaces, archivos demasiado grandes o UTF-8 inválido. Una prueba modifica la copia y verifica el original ficticio intacto.
- La carpeta de trabajo se puede elegir o crear en Configuración y se aplica al reiniciar. Probados persistencia, recuperación de una biblioteca, bloqueo entre procesos, rechazo de una carpeta de originales y destino ausente sin recreación silenciosa. No se trasladan proyectos ni cuentas.
- Generados .deb Linux y NSIS Windows 0.8.3. Verificados 32 archivos de runtime Linux y 98 de Windows, fuentes de Windows idénticas al checkout, binarios y SHA256. El backend del instalador Windows pasó bajo Wine: handshake, HTTP, cierre por stdin y segundo arranque sin bloqueo retenido. No se verificó la interfaz ni la instalación en Windows real.
- El .deb extraído pasó dos arranques Tauri/WebKit en Xvfb: cuatro diálogos distintos de carpeta (seleccionar/cancelar), importación del texto ficticio sin cambiar la fuente, seis operaciones de exportación, editor, navegación, preferencias, llavero y voz simulada. La automatización cuenta diálogos, no teclas: GTK puede consumir Escape en su entrada de ubicación sin cerrar el selector.
- Sin llamadas a IA ni cambios en repositorios de libros. De `cuentos_proyecto_humano` se consultaron nombres y tamaños: 46 archivos de texto (11 en manuscript), ninguno superior a 250 KB. No se importó material real durante las pruebas. Imágenes, PDF/DOCX y metadatos editoriales de otros sistemas no se convierten con esta importación.

# Inicio, libro físico y motores 0.7.0 — 2026-09-09

- Pasaron 31 pruebas de backend y 4 del protocolo Codex. Los seis transportes experimentales se comprobaron con SSE ficticio, errores, truncación, límites, claves y direcciones inválidas, historial y propuestas pendientes sin modificar documentos.
- Pasaron diez recorridos de Chrome: base, UX, configuración, microinteracciones, modos, voz local, OpenAI de voz simulado, Gemini de voz simulado, setup/teclado/libro y motores editoriales simulados. Sin llamadas reales de IA ni cambios en originales.
- Setup: primera apertura, omitir y reabrir, persistencia, cuenta y voz opcionales; navegación por teclado, destinos compartidos, tamaño 6 × 9, estimación por área, 300 páginas crema → 19,05 mm, persistencia y conservación de maquetas manuales antiguas.
- Motor por proyecto y seis proveedores probados desde la UI sin sesión ChatGPT; vuelve a Codex conservando su selector de modelo/esfuerzo. Claves de voz/editorial separadas y ausentes en archivos de proyecto. Cifrado simulado por proveedor comprobado.

- Linux 0.7.0 empaquetado pasó arranque, aislamiento, voz local, cámara denegada, apariencia entre dos arranques y clave ficticia cifrada/recuperada/eliminada en el almacén nativo. Verificados 78 hashes y web idéntica.
- La primera preparación Windows omitía `workbench_providers.py`; la prueba de arranque falló y se corrigió la lista de archivos. El runtime regenerado pasó bajo Wine (backend, guardado, historial, bloqueo y Vosk). Verificados 96 hashes y todos los módulos incluidos. Windows nativo e inferencia real de adaptadores siguen sin validar.

# Persistencia de apariencia y microinteracciones 0.6.1 — 2026-09-09

- La preferencia de modo y ambas paletas continúa en el perfil local del usuario; el arranque la restaura antes de cargar la aplicación principal, sin esperar a abrir un proyecto. No sincroniza preferencias entre cuentas ChatGPT ni equipos.
- Pasaron 27 pruebas de servidor y los recorridos de navegador base, UX, configuración, microinteracciones, modos, voz local, OpenAI simulado y Gemini simulado. La prueba nueva comprueba tema antes del JS principal, espera y bloqueo de repetición, recuperación tras error, progreso sin reemplazo de elemento, señal de finalización sin repetición, movimiento reducido y arrastre 3D sin demora.
- El indicador de espera solo bloquea controles directos: los paneles con varios handlers de clic no interfieren entre sí. Pasaron lectura desde una respuesta del chat y traducción/revisión tras esta corrección.
- Comprobación de voz extendida: el micrófono continúa alternando escucha mientras el permiso/conexión están pendientes; no queda bloqueado por el indicador genérico de espera.
- `tests/desktop_check.py --voice` pasó con Electron Linux 0.6.1: guardó modo oscuro, violeta y rosa en la primera apertura y comprobó las mismas preferencias en la segunda, con otro puerto local. También pasaron aislamiento, voz local y cifrado/recuperación/borrado de clave ficticia. Se verificaron 76 hashes del runtime Linux y archivos web idénticos a las fuentes.
- El runtime Windows 0.6.1 pasó bajo Wine (Python, Vosk, copias, guardado/historial y bloqueo); se verificaron 93 hashes, web y módulos de escritorio idénticos a las fuentes. No equivale a validar instalación o interfaz en Windows nativo.
- Sin llamadas nuevas a ChatGPT ni proveedores de voz, sin cambios en manuscritos originales. La instalación local consultada sigue en 0.5.0; actualizar el paquete necesita contraseña administrativa. Ver [pasada de UX](UX_REVIEW.md).

# Chat, configuración y micrófono 0.6.0 — 2026-09-09

- Recorridos locales de navegador: base, UX, voz local, modos, OpenAI simulado, Gemini simulado y configuración. Se verifican las seis paletas y persistencia/sistema, modales amplios y compactos, chat principal, giro 3D con mouse/teclado, toggle, Espacio, repetición de tecla y liberación al perder foco. Datos ficticios y micrófono virtual.
- `tests/voice_vault_check.cjs`: cifrado inyectado, reinicio, permisos, borrado, corrupción, rutas y rechazo de `basic_text`. No se confunde este doble con el almacén nativo.
- Con clave Gemini autorizada recibida solo por stdin privado: autenticación, token efímero, setup, envío de PCM sintético y respuesta de audio/transcripción reales confirmados. También se observó una acción de tema y consulta de contexto. El chequeo estricto de la orden oral «oscuro» no pasó: en un intento eligió Sistema, en otro consultó contexto. Por eso no se declara validada la fidelidad de órdenes por voz ni éxito de `live_gemini_check.py`. Conexiones cerradas; clave no guardada en archivos. OpenAI real sigue sin probarse.
- Código de escritorio con guardado optativo vía safeStorage; sin fallback de texto plano, restauración sin autoconexión y borrado por proveedor. En este LXQt el autodetector devolvía basic_text: la detección de Secret Service activo permitió cifrar una clave ficticia con gnome_libsecret.

- Pasaron 27 pruebas de servidor y 4 del protocolo stdio. Sintaxis JS/Python y diff sin errores.
- `tests/desktop_check.py --voice` pasó con el paquete Linux 0.6.0 final: UI aislada, voz local, cámara denegada, preferencias, cifrado nativo de clave ficticia, recuperación al reiniciar y eliminación del archivo al olvidar. Una repetición superó el timeout de 55 s durante compresión simultánea; la ejecución final con margen de 120 s pasó ambas aperturas y las aserciones de borrado.
- Windows: Python/Vosk/guardado/historial/bloqueo pasaron bajo Wine. No se presenta como prueba de instalador, GUI, micrófono ni DPAPI en Windows nativo.
- Verificados 75 hashes del runtime Linux y 92 del Windows; web y módulos asar idénticos a las fuentes, sin cuentas/manuscritos/skills globales. Generados instaladores locales 0.6.0 y SHA256SUMS, sin firma ni publicación.
- La instalación local consultada sigue en 0.5.0. La actualización con sudo no interactivo requiere contraseña; el .deb 0.6.0 queda listo para instalar y reiniciar la app.

# Traducción, rol y asistentes de voz 0.5.0 — 2026-09-09

- Pasaron 27 pruebas de servidor y 4 del cliente stdio. Nuevas comprobaciones cubren criterio humano, copias traducidas, conflictos, revisión por versión, exportación, modos antiguos, claves en memoria, consentimiento, exclusión de fuentes retiradas, contratos HTTP y errores de ambos proveedores.
- Pasaron seis recorridos de Chrome: base, UX, voz local, modos, OpenAI Realtime simulado y Gemini Live simulado. Usan ficción, respuestas/transportes externos simulados y micrófono virtual. Cubren acciones permitidas/denegadas, ausencia de aprobación automática, duplicados, mensajes pendientes, cancelación, permisos tardíos, PCM entrada/salida, interrupción de reproducción y liberación de recursos.
- `tests/live_modes_check.py` pasó tres turnos reales de ChatGPT: consulta de matiz con cita/alternativas, traducción tras criterio humano y entrevista de rol con una pregunta. Se usó ficción temporal. No se tocaron libros vecinos.
- La prueba experimental de Realtime con sesión ChatGPT devolvió `realtime conversation requires API key auth`. Se documentó la limitación y se implementaron proveedores API explícitos: OpenAI gpt-realtime y Gemini Live con clave AI Studio. No hubo claves reales ni llamadas de pago; ambos transportes externos siguen pendientes de validación con cuenta/API real.
- `tests/desktop_check.py --voice` pasó en Electron Linux 0.5.0 desempaquetado: backend y UI, aislamiento, DOCX, ayuda de 14 temas, micrófono virtual, cámara denegada, dictado/lectura y preferencias tras reinicio. Verificados sus 74 hashes y los archivos web idénticos al código actual. La excepción de sandbox pertenece solo a esta prueba desempaquetada.
- El runtime Windows incluido pasó bajo Wine: Python, servidor, copias, guardado/historial, bloqueo de instancia y Vosk español. Verificados 91 hashes y fuentes idénticas. No equivale a instalación, interfaz o voz online probadas en Windows nativo.
- Generados los instaladores locales 0.5.0 Linux `.deb` y Windows `.exe`, con `dist/installers/SHA256SUMS`. Sin firma ni publicación. La versión instalada verificada con dpkg sigue siendo 0.3.0; no se actualizó automáticamente.
- Una corrección final hace que la tarjeta del chat refleje la revisión aprobada de una traducción incluso cuando el texto no cambia; el recorrido de modos volvió a pasar.
- Ver [alcance de modos](MODES.md) y [voz, privacidad, facturación y fuentes oficiales](REALTIME.md). Los resultados anteriores se conservan debajo como historial.

# Ayuda y usabilidad 0.4.0 — 2026-09-09

- Pasaron las 4 comprobaciones del protocolo y las 19 de almacenamiento/HTTP/modelos/plan/exportación/voz. Sintaxis Python/JS y `git diff --check` correctos.
- `tests/ux_browser_check.py` pasó: ayuda disponible sin proyecto ni cuenta, sin escrituras ni llamadas IA al abrir; búsqueda sin tildes y sin resultados; F1/Escape y retorno del foco; editor y ficha pendientes preservados; mensaje y tarea conservados por proyecto al recargar; texto nuevo preservado durante una respuesta HTTP simulada; error visible después de 12,5 segundos; cancelación de creación; lectura del chat sin saltos; biblioteca plegable y ausencia de desbordamiento horizontal a 390 px. También demora la carga de ayuda para comprobar que la app espera a sus scripts antes de abrir un proyecto.
- Pasaron los recorridos `tests/browser_check.py` y `tests/voice_browser_check.py` después de los cambios finales. La prueba editorial incluye selección de modelo/esfuerzo desplegando sus ajustes. No se consumió cuota ChatGPT ni se grabó al usuario en este corte.
- Capturas inspeccionadas a 1440 y 390 px, en temas claro y oscuro. Esta pasada no equivale a pruebas con lectores de pantalla ni a validación WCAG completa.
- `tests/desktop_check.py --voice` pasó en Electron Linux 0.4.0 desempaquetado: ayuda abierta y cerrada, API/exportación DOCX, renderer aislado, micrófono virtual, cámara denegada, dictado y síntesis incluidos, preferencias conservadas al reiniciar. Usa la excepción de sandbox exclusiva del test; no se declara una prueba de instalación 0.4.0.
- Windows bajo Wine: el Python incluido pasó `windows_runtime_check.py` con copias ficticias, guardado/historial, bloqueo de segunda instancia y Vosk nativo con PCM de silencio. No se validaron instalación, interfaz, micrófono ni System.Speech en Windows real.
- Verificados 71 hashes del runtime Linux y 86 del Windows, incluida la ayuda; sin cuentas, proyectos ni skill global.
- Generados localmente los instaladores **0.4.0** Linux `.deb` (231,4 MiB) y Windows `.exe` (245,2 MiB), con SHA256SUMS en `dist/installers`. Sin firma ni publicación.
- Estado instalado comprobado con dpkg: **0.3.0**. La instalación que antes esperaba autenticación se completó; no se actualizó automáticamente a 0.4.0.

Ver [hallazgos y mejoras aplicadas](UX_REVIEW.md). Los resultados históricos siguientes corresponden a sus versiones y fechas; no se repitieron las llamadas reales a modelos ni la prueba nativa del motor de voz para este cambio de interfaz.

---

# Entrevista y voz local 0.3.0 — 2026-09-08

- Comprobaciones ejecutadas: 4 del protocolo y 19 de almacenamiento/HTTP/modelos/plan/exportación/voz; pasaron. Sintaxis Python/JS y `git diff --check` correctos.
- Chrome: recorrido editorial completo, modelo y esfuerzo por proyecto, borrador con guardado explícito sin duplicación, plan/orden/meta/estados/fichas, exportación y persistencia; pasó. Deshacer/Rehacer nativos para texto, después de guardar y para formato; cambiar de documento no trasladó su pila de edición. El test respeta la agrupación de operaciones de Chromium.
- La entrevista es la opción predeterminada del wizard. En modo guiado el chat ocupa el centro y el material se abre con un control explícito; los proyectos existentes conservan su forma de trabajo.
- Modelos reales: `tests/live_model_check.py` completó un turno con gpt-5.6-luna/medium y otro con gpt-5.6-sol/high, usando la sesión ChatGPT existente y ficción temporal. Conservó el mismo hilo y el nombre de la protagonista sin guardar manuscritos automáticamente. El catálogo de la interfaz se obtiene de Codex, no de esta lista de prueba.
- `tests/voice_browser_check.py` pasó: dispositivo de micrófono virtual de Chromium, captura PCM, dictado añadido al mensaje sin envío, descarte, rechazo de permiso, lectura y lectura automática una vez por nueva respuesta. Reconocimiento y síntesis se simulan en esta prueba de UI; nunca se grabó al usuario.
- `tests/live_voice_check.py` pasó con Vosk/modelo español y eSpeak NG reales: sintetiza una frase ficticia y reconoce palabras de ella, sin red ni micrófono. Hubo errores de transcripción (por ejemplo, «barco» perdió su terminación), por lo que no se afirma exactitud general ni calidad de voz natural. La primera versión del fixture con remuestreo por vecino cercano falló; se corrigió a interpolación lineal y se volvió a ejecutar.
- DOCX: paquete/XML verificados por tests; LibreOffice abrió y convirtió un libro ficticio exportado, conservando texto Unicode y excluyendo canon/referencias. Esto no comprueba maquetación de imprenta ni compatibilidad visual completa con Word.
- Linux empaquetado: `tests/desktop_check.py --voice` pasó con renderer aislado, exportación DOCX, permiso de audio concedido al micrófono virtual, cámara denegada, WAV de síntesis, dictado nativo incluido y persistencia al reiniciar. El test desempaquetado usa --no-sandbox; la comprobación de instalación se registra aparte.
- Paquetes 0.3.0 generados: Linux .deb de 231,4 MiB y Windows .exe de 245,2 MiB, con SHA256SUMS. Sin firma ni publicación.
- Windows bajo Wine: el backend, guardado/historial/lock y Vosk nativo con modelo español pasaron; el fixture fue PCM de silencio. Un primer lanzamiento con pipes produjo WinError 6 de Wine antes de iniciar Python; con terminal válida pasó. No se validaron interfaz, micrófono, lectura System.Speech ni instalación en Windows real.
- Instalación local: la 0.2.0 se instaló y pasó una prueba real con sandbox habilitado. La actualización a 0.3.0 está preparada y solicitada mediante pkexec/apt; al cerrar estas comprobaciones sigue esperando autenticación gráfica del sistema. No se declara instalada la 0.3.0 todavía.
- Runtimes: 70 hashes Linux y 85 Windows verificados; sin cuentas, proyectos, conversaciones ni skill global. Dictado español incluido con SHA256 fijados y avisos de terceros; lectura Linux como dependencia del sistema.

La comparación documental y todas las mejoras propuestas para este corte están en [PRODUCT_IMPROVEMENTS.md](PRODUCT_IMPROVEMENTS.md). No se ejecutaron aplicaciones competidoras ni se modificaron libros originales.

---

# Corte de escritorio 0.2.0 — 2026-09-08

- Generados localmente `Story-Workbench-0.2.0-linux-amd64.deb` y `Story-Workbench-0.2.0-win-x64.exe`. Electron 44.3.0, Codex 0.153.4, Python Linux 3.12.3 / Windows embebible 3.14.7. Paquetes sin firma ni publicación. SHA256SUMS acompaña a los archivos en dist/installers.
- Checks ejecutados: 4 pruebas del protocolo inicial y 13 pruebas de almacenamiento, HTTP, autenticación simulada y validación de maqueta; todas pasaron. Sintaxis JS/Python y git diff --check correctos.
- Chrome/Playwright: wizard, entrevista simulada, edición, conflictos, historial, aceptación por bloque, exportación, temas, progreso parcial en fallo, colapsado/visto persistido, giro y medidas 3D, carga de imagen local, guardado y recuperación de maqueta, ancho móvil; pasó. La imagen de prueba fue ficticia, no una portada privada.
- Electron Linux empaquetado: renderer sin Node, protocolo local, creación de proyecto ficticio por HTTP y preferencia persistida al reiniciar con otro puerto; pasó. Usa una excepción --no-sandbox únicamente en el test desempaquetado, por restricciones de namespaces del equipo. El producto conserva sandbox:true y el .deb contiene los scripts de configuración de sandbox/AppArmor. No se ejecutó su instalación como root.
- Windows: el Python incluido cargó el backend bajo Wine. `windows_runtime_check.py` comprobó creación, guardado atómico, historial y exclusión de una segunda instancia bajo Wine. El intento de abrir Electron Windows bajo Wine agotó 55 segundos con errores de red/DirectComposition de Wine; no se declaró exitoso. No equivale a ejecución nativa en Windows; instalación, desinstalación, login y sandbox en Windows real quedan pendientes.
- Login real: se recibió la URL oficial y se canceló correctamente en un CODEX_HOME temporal vacío, también con el Codex incluido en el paquete Linux. Completar OAuth con una cuenta nueva se comprobó con un doble del protocolo, no se autenticó otra cuenta real.
- Entrevista real: dos turnos con build-novel local y dos con la guía integrada, usando la sesión ChatGPT existente y ficción temporal. Ambos conservaron contexto, hicieron una pregunta por turno y no crearon manuscritos. Para probar ausencia de skill se desactivó solo su descubrimiento con un doble; las respuestas fueron de ChatGPT real.
- Ambos runtimes: hashes del manifiesto verificados, sin auth.json, config.toml, SKILL.md, project.json ni HANDOFF.md. App ASAR limitado a main y metadatos. No se tocaron libros vecinos ni se incluyeron credenciales o material privado.
- npm install informó cero vulnerabilidades conocidas; npm audit --omit=dev también. Esto no sustituye una revisión de seguridad de las dependencias nativas.

Ver [instalación, datos y límites](DESKTOP.md). Los resultados históricos siguientes pertenecen a los cortes anteriores.

---

# MVP: resultados y alcance

Comprobado el 2026-09-08 en Linux, Python 3.12, Codex CLI 0.153.4 y Chrome con Playwright. Casos ficticios; sin manuscritos privados, API de pago ni cambios en libros originales.

## Prueba real con ChatGPT

`python3 tests/live_mvp.py` completó:

1. Perfil de permisos: bloqueó lectura de un archivo ficticio no seleccionado, un symlink que apuntaba fuera de la carpeta del agente y un intento de escritura. Permitió arrancar el ejecutable de Codex y Python necesarios para la comprobación. El producto no expone `command/exec` por HTTP.
2. Diagnóstico: identificó la contradicción «llave azul / llave roja» entre las fuentes; el documento quedó intacto.
3. Reinicio: un nuevo gestor y un nuevo proceso App Server reanudaron el mismo hilo y recordaron una clave ficticia no repetida en la pregunta.
4. Propuesta: recibió salida estructurada, validó pasajes y fuentes, dejó el documento intacto hasta aceptar un bloque explícitamente y conservó su versión anterior.
5. Cancelación: el gestor interrumpió una respuesta real y recibió estado `interrupted`.
6. Contexto: retirar una fuente produjo un hilo nuevo.

La skill build-novel se descubrió e invocó desde la instalación local. No se distribuyó. Esto verifica la integración y un ejemplo editorial acotado; no demuestra calidad literaria general ni detección exhaustiva de impactos.

## Pruebas locales y navegador

- Las cuatro comprobaciones originales del cliente stdio pasan.
- Ocho comprobaciones del MVP cubren guardado/conflicto/restauración, cambios externos, rutas y symlinks, validación íntegra de propuestas, rechazo de propuestas desactualizadas, aceptación separada de bloques, decisiones, separación de proyectos, recuperación tras reinicio, límite de contexto, autenticación HTTP, Host/Origin, exportación y exclusión de un segundo servidor sobre los mismos datos.
- El recorrido de Chrome verificó: crear demo, editar/guardar/restaurar, detectar edición externa sin perder borrador, aceptar una propuesta de prueba, registrar decisión, importar copia, impedir ejecución de HTML en la vista previa, modo foco, descargar ZIP, recargar y cambiar a un universo vacío. También comprobó ausencia de errores JavaScript y desbordamiento horizontal a 390 px.
- La captura del navegador fue inspeccionada a 1440 × 1000. Diseño adaptable con biblioteca, documento y asistente. Los casos de prueba y las capturas usan exclusivamente ficción.

## Distinciones necesarias

- El chat recibe fuentes serializadas; la UI informa **enviadas**, sin inventar evidencia de lectura por herramientas.
- El historial del navegador y los metadatos permiten recuperar decisiones y conversaciones. No hay una base de conocimiento ilimitada: fuentes/decisiones demasiado grandes provocan un error visible.
- Un resumen es una referencia provisional con hashes de las fuentes. Las fuentes del historial indican si cambiaron desde el envío; no se sincronizan traducciones automáticamente.
- Diagnóstico y propuesta son acciones distintas. La API valida que cada propuesta afecte un pasaje único del contexto capturado y que la versión no haya cambiado al aceptar.
- La cuota agotada se prueba con eventos sintéticos en el cliente original. No se agotó la cuenta real ni se simuló una caducidad real de OAuth.
- No se hizo una auditoría de accesibilidad completa, una evaluación de lectores ni una prueba prolongada sobre libros enteros. La imagen ambiental es local y temporal; no hay generación de imágenes.

Protocolo contrastado con los esquemas generados por la versión instalada y la [documentación oficial de App Server](https://learn.chatgpt.com/docs/app-server). El perfil de acceso sigue las [reglas oficiales de permisos](https://learn.chatgpt.com/docs/permissions); la configuración específica se comprobó ejecutándola.

## Inicio de proyecto y entrevista guiada

El wizard permite elegir escritura directa (manuscrito vacío, sin llamada IA) o creación guiada (proyecto sin documentos, chat central e inicio automático de build-novel). Conserva la elección y el historial por proyecto. Los proyectos anteriores se abren en modo escritura.

Comprobado con `python3 tests/live_mvp.py --interview-only`: la skill y su referencia de entrevista se cargaron desde la instalación local; la primera respuesta formuló una sola pregunta y la segunda continuó a partir de la respuesta del autor, con el mismo hilo tras reiniciar el gestor. No creó manuscritos ni duplicó la bienvenida.

Diez pruebas del MVP y las cuatro del cliente stdio pasan. El recorrido de Chrome usa un doble explícito para las respuestas de entrevista: comprueba wizard/cancelación/retroceso, creación sin fuentes, chat en el centro, respuesta del autor, recarga sin inicio duplicado, foco y cambio de modo. La integración real se comprueba por separado con el comando anterior; no se confunden las respuestas simuladas del navegador con respuestas del modelo.

Los instaladores finales Electron 0.7.0 Linux/Windows se generaron con SHA256 local. La comprobación ASAR confirmó módulos de escritorio iguales a fuentes y metadatos 0.7.0; electron-builder elimina configuración de desarrollo del package.json empaquetado. El inicio posterior de Tauri y sus resultados están en [TAURI_MIGRATION.md](TAURI_MIGRATION.md).

## Tauri 0.8.0 como único escritorio — 2026-09-09

- Electron y electron-builder retirados de dependencias, shell y pruebas específicas. Preparación pública directa de Python/Codex/Vosk; no requiere una build Electron anterior. Instaladores reproducibles con `desktop/build.py` y el entorno Docker fijado; sin remoto ni publicación. HANDOFF privado, proyectos y credenciales quedan fuera del commit y los paquetes.
- Nombre Story Workbench y carpeta histórica de configuración: conserva proyectos y sesión Codex de Electron. Nuevo perfil web y llavero; preferencias y claves anteriores no se convierten automáticamente. El usuario configura esas opciones una vez. Sin lecturas ni modificaciones de los repositorios de libros vecinos.
- Exportación nativa autenticada, nombre validado, escritura atómica y Cancelar sin escribir. Se envían bytes por el protocolo local: las pruebas con Blob y POST sin cuerpo provocaron una caída en WebKitGTK; el flujo final con bytes, también para un archivo vacío, pasó. No se relajó CSP ni el sandbox.
- Cierre cancelable por cambios sin guardar o tarea en curso. Cuatro pruebas Rust pasaron: orígenes/handshake, frontera de credenciales, separación de proveedores y nombre/escritura de exportaciones. Pasaron las 32 pruebas Python del backend. `desktop_bridge_check.py` pasó con Guardar, Cancelar, error visible y cancelación del cierre; usa funciones compatibles con la CSP, sin unsafe-eval.
- El binario extraído del .deb pasó dos arranques en este Linux con perfil ficticio y llavero temporal: editor, navegación, temas, libro 6 × 9, exportación DOCX real por diálogo GTK, Cancelar y archivo vacío, audio virtual, cámara denegada y lectura local/online simulada. No hubo cuenta ChatGPT ni llamadas API. Las claves ficticias se limpiaron del llavero.
- Se mantiene el límite de WebRTC de este WebKit: la conversación oral OpenAI no está disponible por ese transporte. La lectura OpenAI/Gemini y Gemini oral se comprobaron con transporte simulado. No se afirma autenticación, calidad ni sesión real con proveedores.
- Windows compila mediante MSVC/cargo-xwin y NSIS. Python Windows y Vosk pasaron bajo Wine: corpus ficticio, guardado, historial, bloqueo y PCM de silencio. El lanzador y los recursos extraídos de NSIS pasaron handshake, HTTP y cierre por stdin en dos arranques. La prueba usa tres pipes, como el plugin Shell; los handles de la primera prueba bajo Wine no eran válidos para Python. Esto no valida la interfaz WebView2 ni el llavero Windows en un equipo real.
- La auditoría PE detectó VCRUNTIME140 en el lanzador inicial; se cambió a CRT estático y se añadió una comprobación que rechaza esa dependencia externa. Python conserva su runtime oficial incluido en su propio directorio. Linux declara glibc >= 2.38, requerida por el Python empaquetado, y xdg-utils para abrir el navegador. NSIS incluye bootstrapper WebView2 y ofrece español/inglés; falta firma de editor.

La comprobación final `installer_check.py` pasó con 32 archivos Linux y 97 Windows, incluyendo cada MANIFEST.json. Verificó integridad, ausencia de directorios de cuenta/proyecto, fuentes Windows actuales, el lanzador incluido y ausencia de VCRUNTIME/MSVCP externos en los ejecutables de la app. El .deb definitivo volvió a pasar ambos arranques y seis diálogos; el lanzador estático extraído del NSIS definitivo pasó dos arranques bajo Wine.

- `Story-Workbench-0.8.0-linux-amd64.deb`: 192984018 bytes; SHA256 `7b0a70375f02ac04bfdf1c8804bce029f102b1a4aa8cebd574b7b128a03f0b77`.
- `Story-Workbench-0.8.0-win-x64.exe`: 208549705 bytes; SHA256 `70c77bd67302c42e0a1d5bd257badf72ee7db9cd521faf4c3a657669f869e55e`.

No se instaló sobre la app del usuario ni se tocaron sus manuscritos. Los paquetes son locales y sin firma; la instalación y la interfaz en Windows real siguen sin validación.

## Tauri 0.8.1: inicio, temas y lectura automática — 2026-09-09

- Inicio de cuatro pasos: tema, cuenta, voz opcional y proyecto. Una sola lista de temas compartida con Configuración, Sistema inicial, preferencias anteriores conservadas y elección recordada incluso al omitir el inicio. Retirado el badge «Local y privado».
- Avisos dentro del diálogo abierto encima de los demás, siguiendo el orden real de apertura. El error de consentimiento de voz se muestra sin blur y con anuncio accesible; también al volver al wizard.
- Casilla «Leer respuestas» junto al micrófono, agrupada también en ventanas estrechas. Usa el proveedor de voz autorizado y TTS local de respaldo. Desmarcar detiene la lectura; no reproduce historial y cambiar de proyecto la desactiva. Si llega una respuesta durante dictado local, espera; si hay conversación oral, la cierra para narrar sin eco y se puede retomar pulsando el micrófono.
- Pasaron `browser_check.py`, `setup_browser_check.py`, `settings_browser_check.py`, `motion_browser_check.py`, `voice_browser_check.py` y `reading_browser_check.py`: flujos principales, temas/persistencia/sistema, error real de consentimiento sobre modales anidados a 1440/390 px, teclado, micrófono virtual, lectura única, espera de dictado, cancelación y respaldo local. Gemini/OpenAI simulados, sin llamadas API ni claves reales. Capturas de modal móvil y compositor inspeccionadas.
- El `.deb` 0.8.1 extraído pasó `tauri_check.py` en este Linux en dos arranques: wizard con tema primero, error visible dentro de voz, lista única, casilla en el compositor, persistencia, llavero temporal, audio simulado y seis acciones de exportación mediante diálogos GTK reales. Se mantiene la limitación WebRTC de la conversación OpenAI en este WebKit; no afecta la lectura por WebSocket.
- El backend del instalador Windows pasó dos arranques, HTTP y cierre por stdin bajo Wine. No se validó la instalación ni la interfaz en Windows real. `installer_check.py` verificó 32 archivos de runtime Linux y 97 Windows, correspondencia con el código y SHA256 de ambos instaladores. Paquetes sin firmar ni publicar.
- `Story-Workbench-0.8.1-linux-amd64.deb`: 192984904 bytes; SHA256 `ad18572c43d40d439cb7cf9399bfb0fbe5befe5301743c410064ea3344b3c7f0`.
- `Story-Workbench-0.8.1-win-x64.exe`: 208552011 bytes; SHA256 `b4e47a00f987b5a3c88cfbc88e82c6ccb298a9cb187625485a383429ab729f43`.

## Tauri 0.8.2: volumen y diagnóstico de lectura Gemini — 2026-09-09

- Volumen de voz 0–100% en Configuración, persistido por usuario, con teclado y estado Silenciado. Afecta al PCM de Gemini/lectura OpenAI, al audio de conversación OpenAI y al TTS local; no cambia la captura del micrófono.
- Lectura Gemini con voz Kore explícita. WebSockets binarios como ArrayBuffer y decodificación directa. No se anuncia «Leyendo» hasta recibir muestras no silenciosas. Turno vacío o solo silencio activa respaldo; 15 segundos sin voz también lo activa con aviso de audio ausente. La activación del AudioContext puede cancelarse y queda dentro del plazo de preparación de 30 segundos.
- Prueba real autorizada con clave por stdin sin eco, solo en memoria, frase ficticia y sin guardar audio: se completaron lecturas Gemini en Chrome con unos 3,4 segundos de PCM no silencioso, tanto con la configuración previa como con Kore. También se observaron turnos vacíos y esperas sin audio, en Chrome y WebKitGTK. WebKit recibió voz real con Kore en otro intento, pero no completó la lectura durante el plazo de 60 segundos del ensayo. **No se declara resuelta la estabilidad de Gemini Live.**
- La hipótesis inicial de autoplay no explica por sí sola el fallo: un WebKit genérico puede suspender el AudioContext, pero Tauri/Wry ya configura una política de sitio que permite reproducirlo. No se cambió esa política en producción.
- Pasaron los cuatro tests de `test_realtime` y los checks de navegador de lectura, Gemini, OpenAI Realtime y dictado: clave/consentimiento, voz explícita, volumen, PCM binario, silencio/vacío, espera de 15 segundos, cancelación de activación suspendida, respaldo local y persistencia. Proveedores simulados en estas comprobaciones.
- El `.deb` final pasó dos arranques de Tauri/WebKitGTK en Xvfb: volumen 35% conservado, ganancia PCM aplicada, lectura simulada y seis operaciones de exportación GTK. Los intentos con escritorio compartido dieron resultados inconsistentes en la automatización del foco; se comprobó en pantalla aislada y el driver ahora usa foco directo sin depender del gestor de ventanas.
- El backend Windows empaquetado pasó dos arranques/HTTP/cierre bajo Wine. `installer_check.py` verificó 32 archivos Linux, 97 Windows y SHA256 de ambos instaladores. Windows nativo sigue pendiente; paquetes sin firma ni publicación.
- `Story-Workbench-0.8.2-linux-amd64.deb`: 192983650 bytes; SHA256 `e2b37ca16fdebfe41a7e356047fbc8e1f6d90461bf05d00b4d6ebea221cfe81d`.
- `Story-Workbench-0.8.2-win-x64.exe`: 208555387 bytes; SHA256 `510254dfc3a0a81c3e16053732326199d33d97f58f6ad6fbc7488bdc76a4c7e2`.
