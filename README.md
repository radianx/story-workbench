# Story Workbench

Un espacio local para escribir y revisar historias con IA, conservando el control del autor. Nombre provisional.

**Estado: MVP de escritorio Tauri 0.9.0**, 2026-09-10. Editor, fuentes, conversaciones con Codex y revisión por bloques comprobados con material ficticio. No se modificaron los repositorios de libros.

## Contribuir

La [guía de contribución](CONTRIBUTING.md) incluye un arranque sin cuenta ni claves, mapa del código, pruebas y primeros aportes posibles. Se aceptan reportes y propuestas en español o inglés; hay plantillas de issues y pull requests. Para vulnerabilidades, ver [SECURITY.md](SECURITY.md). El código propio se distribuye bajo la [licencia MIT](LICENSE); las dependencias conservan sus propias licencias.

El workflow `Checks` está preparado para comprobar Python, JavaScript y cinco recorridos de navegador con ficción y proveedores simulados. El uso inválido de `runner.temp` en el entorno del job se corrigió mediante un paso que prepara `CODEX_HOME`; el workflow pasó `actionlint`, pero su nueva ejecución en GitHub queda por verificar; no necesita secretos ni publica instaladores.

## Instalar la app de escritorio

Los paquetes locales están en `dist/installers/`. Ver [distribución y comprobaciones](DESKTOP.md) para los límites de validación de cada sistema.

1. **Linux x64 (Ubuntu 24.04+):** abrí el archivo `.deb` con el instalador de aplicaciones del sistema e instalalo. **Windows x64:** abrí el `.exe` y seguí el asistente de instalación.
2. Abrí **Story Workbench** desde el menú de aplicaciones.
3. El asistente inicial comienza por el tema de la app y permite conectar ChatGPT, preparar voz opcional y crear o abrir un proyecto. Se puede omitir y reabrir desde Configuración. Para conectar: **Cuenta ChatGPT → Conectar ChatGPT → Abrir inicio de sesión seguro**. Completá el acceso en tu navegador y volvé a la app.

Usa Tauri e incluye Python y Codex: el usuario no necesita terminal ni instalarlos por separado. Cada instalación usa la cuenta del autor que la abre. Se puede escribir sin iniciar sesión; la IA necesita internet y disponibilidad de Codex en esa cuenta. Codex con ChatGPT es el motor editorial principal, sin fallback de pago. Se pueden elegir seis adaptadores experimentales con clave propia o servidor local; ver [motores](PROVIDERS.md). La voz online opcional admite claves de OpenAI o Gemini con condiciones y facturación API separadas; el dictado local sigue disponible. Windows instala WebView2 si falta (requiere internet); Linux usa WebKitGTK del sistema. Los paquetes son preliminares y no están firmados ni publicados.

**Archivar proyecto** lo retira de Tu biblioteca sin borrar archivos. **Proyectos archivados** permite recuperarlo. Modelo y esfuerzo se eligen junto al tipo de tarea, debajo del mensaje. **Enter** envía el mensaje y **Shift+Enter** inserta un salto de línea; Ctrl/Cmd+Enter también sigue disponible.

## Iniciar desde el código

Requiere Python 3.11+ y Codex CLI con sesión ChatGPT para el asistente. La biblioteca y el editor funcionan sin conectar Codex. El servidor usa biblioteca estándar de Python; PDF e imágenes requieren las dependencias fijadas en `requirements.txt` (incluidas en los instaladores). El dictado necesita los recursos nativos de voz preparados al construir el escritorio; en Linux, la lectura usa espeak-ng (el .deb lo instala como dependencia).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m src.app
```

En Windows: `.venv\Scripts\python.exe` en lugar de `.venv/bin/python`. El código Python de la aplicación vive en `src/`; los datos siguen en `private/workbench/`.

Para preparar el dictado al ejecutar desde código: `python3 desktop/prepare_voice.py --target linux` (descarga recursos públicos). La instalación `.deb` ya incluye el modelo y resuelve la dependencia de lectura del sistema.

Abrí **el enlace completo que imprime la terminal**: incluye una clave temporal de acceso local en el fragmento. Solo escucha en `127.0.0.1:8765`. Detener con Ctrl+C. Después de reiniciar, abrí el nuevo enlace; los proyectos y las conversaciones siguen guardados. Para otro puerto: `python3 -m src.app --port 8766`.

Elegí «Explorar un proyecto ficticio» para empezar con cuatro fuentes que contienen una contradicción conocida. O creá un proyecto: el asistente pide un nombre y el objetivo. Para historias y rol conserva el punto de partida; para traducción requiere una obra existente y los idiomas de origen/destino, con detección local corregible. «Escribir por mi cuenta» abre un manuscrito en blanco. «Crear conversando», opción predeterminada, pone el chat en el centro, permite abrir el material con «Ver material» e inicia una entrevista editorial (usa build-novel si está instalada), una pregunta por vez, incluso sin documentos. También podés importar copias de Markdown/TXT UTF-8, EPUB sin DRM y DOCX (hasta 15 MB por archivo). La importación conserva texto y orden de lectura; divide unidades de más de 250 KB y requiere revisar el resultado. No importa imágenes, comentarios ni maquetación. Los originales quedan en su lugar; la app no acepta rutas de libros ni los reorganiza.

Desde **Importar carpeta…** (Inicio o Configuración) podés revisar y copiar hasta 100 Markdown/TXT de una carpeta, incluidos sus subdirectorios. Conserva las rutas relativas en los nombres; `manuscript`/`manuscrito` se reconocen como manuscrito y el resto como referencia. No importa imágenes, PDF, DOCX, archivos ocultos o enlaces, ni interpreta automáticamente canon, decisiones o conversaciones de otro sistema. Las copias quedan sin seleccionar para IA salvo la primera unidad de una traducción.

**Configuración → Carpeta de trabajo** permite elegir una carpeta vacía o un espacio de la app y crear una subcarpeta. La elección se recuerda para el próximo arranque; no mueve los proyectos existentes. Para volver a ellos, elegí su ubicación anterior. Cuentas y claves permanecen en su perfil habitual.

## Funciones disponibles

| Área | Qué hace el MVP |
| --- | --- |
| Inicio guiado | Wizard de dos pasos con entrevista como opción predeterminada; escritura directa o entrevista editorial con build-novel local o la guía integrada. La forma de trabajo se guarda por proyecto y se puede cambiar desde la biblioteca. Recargar no duplica la bienvenida; una entrevista fallida o interrumpida puede retomarse. |
| Ayuda | Sección opcional con búsqueda, catorce temas desplegables, F1 y enlaces desde cada área. Explicaciones de tareas antes de enviar; recordatorios con puntero y descripciones para lector de pantalla. No abre tours ni llama a IA. |
| Biblioteca | Varios proyectos, documentos nuevos e importados, búsqueda en nombre y contenido, nombre editable y roles: manuscrito, canon, estilo, referencia, planificación y traducción. |
| Contexto | Selección explícita de fuentes, contador de tamaño, nombres y hashes del material enviado. No recorta fuentes en silencio. Retirar o agregar fuentes abre hilo nuevo para evitar conservar material retirado en el historial del agente. |
| Escritura | Editor Markdown, formato básico, vista previa segura, palabras y tiempo de lectura, atajo Ctrl/Cmd+S, modo foco con Ctrl/Cmd+Shift+F, botones Deshacer/Rehacer y atajos Ctrl+Z/Ctrl+Shift+Z (Cmd en macOS). Texto y formato usan el historial nativo del editor; al cambiar de documento o recargar, recurrir a Historial para las versiones guardadas. |
| Recuperación | Borrador por documento y mensaje no enviado por proyecto durante la sesión de la ventana, guardado atómico, conflicto ante cambios externos, versiones anteriores y restauración recuperable. |
| Asistente | Cuenta ChatGPT administrada por Codex; conversación, diagnóstico, análisis de impacto hipotético, propuestas y resumen para retomar. Respuesta incremental con formato Markdown (títulos, énfasis, listas, citas, código, enlaces y tablas), detención e hilo persistente por proyecto. |
| Plan y avance | Tarjetas de capítulos o escenas sobre los manuscritos, sinopsis, POV, orden y filtro por estado; meta de palabras y progreso de revisión. Cambiar un texto revisado invalida esa marca. |
| Fichas | Plantillas propias de personaje, mundo, voz y arco; documentos provisionales inicialmente sin seleccionar para IA. |
| Voz | Botón Probar voz del proveedor con diagnóstico de audio y sin respaldo local durante la prueba. Dictado local en español, hasta 45 segundos por captura, transcripción editable antes de enviar, descarte y apagado del micrófono al cambiar de proyecto. Lectura con OpenAI TTS o Gemini TTS cuando están autorizados, TTS local de respaldo, opción Siempre voz local y detención; volumen persistente en Configuración y casilla Leer respuestas debajo de Enviar para lectura automática de respuestas nuevas. No abre el micrófono. |
| Voz online opcional | Voz del chat con OpenAI Realtime o Gemini Live: transcripción al mismo chat y lectura de su respuesta; micrófono pausado durante tarea y lectura. Controles de la app queda como modo separado para navegar y preparar tareas. Claves en memoria o cifradas opcionalmente con el almacén del sistema en escritorio, sin fallback. Ver [condiciones y validación](REALTIME.md). |
| Traducción | Inicio con original obligatorio e idiomas elegibles/detectables; unidades de hasta 12.000 caracteres sin omitir texto. Entrevista de intención, encargo y glosario; consultas de matiz con cita y alternativas, criterio humano, comparación y aprobación de copia separada, revisión vinculada a versión y exportación Markdown/DOCX/PDF de unidades aprobadas. |
| Rol (extra) | Entrevista para mundo de mesa, PNJ, facciones, lugares, reglas propias y ganchos abiertos; seis fichas adicionales, material provisional y dossier ZIP. No ejecuta partidas. |
| Equipo editorial | Optativo por mensaje con Codex: modelo/esfuerzo separados, máximo 1–3 colaboradores, reparto y síntesis del principal, panel ciego y aviso de consumo. Aportes colapsables; cancelación conjunta. Experimental. |
| Conversaciones | Nueva conversación vacía el chat y su contexto; anteriores consultables en un desplegable de la biblioteca. Conserva fuentes, decisiones, propuestas y mensajes sin enviar. |
| Modelos | Catálogo de la cuenta ChatGPT y esfuerzos compatibles; selección por proyecto, comprobación al enviar y modelo/esfuerzo efectivo en cada respuesta. |
| Creación | Redacción guiada y botón explícito para guardar como nuevo borrador provisional; repetirlo abre la misma copia. |
| Seguimiento | Baja al final cuando aparece un mensaje o llega texto nuevo del agente; permite volver a la última respuesta después de desplazarte manualmente. Avisos de la sesión, orientación de traducción/rol y progreso de la tarea en su propia pestaña, con contador y limpieza de notificaciones; los errores de formularios permanecen dentro de ellos. Biblioteca plegable a 600 px o menos en modo guiado. Barra de cuatro etapas reales por tarea, sin estimar el porcentaje del libro. Respuestas colapsables con resaltado Nuevo y Marcar como visto; conserva estado al recargar. |
| Motores alternativos | OpenAI API, Gemini, Anthropic, DeepSeek, Kimi y servidor local compatible, experimentales; proveedor por proyecto, claves aisladas y respuestas sujetas a las mismas aprobaciones. |
| Libro 3D | 6 × 9 pulgadas iniciales; lomo según páginas estimadas o reales y papel blanco/crema, con opción manual. Maqueta giratoria de portada, lomo, contraportada y páginas. Medidas en milímetros, título, autor e imágenes locales guardadas por proyecto. Es visual, no un archivo listo para imprenta. |
| Imágenes de Codex | Pedidas en el chat con la sesión ChatGPT: miniatura, visor con zoom, descarga original y conservación provisional en historial y galería. Sin clave API. Disponible en el código posterior a 0.9.0. |
| Imágenes API · experimental | Configuración → Generación de imágenes prepara proveedor preferido y clave API; OpenAI y Gemini son adaptadores experimentales con coste API separado. Desde Imágenes: descripción explícita, vista previa, descarte, guardado humano, descarga original PNG/JPEG y aplicación opcional a la portada 3D. No envía manuscritos ni conversaciones automáticamente. |
| Revisión | Antes/después por bloque; aceptar o rechazar. Solo aceptar cambia la copia local y selecciona el texto resultante en el editor. Propuestas desactualizadas fallan sin sobrescribir. |
| Continuidad | Registro manual de decisiones aprobadas, pendientes y rechazadas, registro de aceptaciones, resumen guardable como referencia provisional con fuentes. |
| Tipografía | Cinco familias locales: Sistema, Arial/Liberation Sans, Georgia, Times New Roman/Liberation Serif y Courier New/Liberation Mono. Vista inmediata, persistencia por usuario y aplicación antes del primer pintado; sin fuentes remotas. |
| Apariencia | Neón y Vice City claros/oscuros, editor de colores y temas JSON compartibles ([formato](THEMES.md)). Tema Sistema por defecto; sigue los cambios claro/oscuro del equipo. También permite elegir Claro u Oscuro y recordar el modo y ambas paletas para el usuario local, también al reiniciar la app; se restauran antes de mostrar la interfaz. |
| Ambiente | Opacidad ajustable y persistente de 0 a 100%. Imagen PNG/JPEG/WebP elegida en el equipo, tenue y sin transmisión a Codex. Dura en la pestaña y se retira al cambiar de proyecto. |
| Exportación | Markdown del documento, incluido su borrador; ZIP del proyecto guardado con documentos y manifiesto de nombres, roles y decisiones. No exporta conversaciones. Desde Plan y avance: libro completo en orden a Markdown, DOCX y PDF de lectura paginado (tamaño guardado o 6 × 9 pulgadas). El ZIP incluye las imágenes generadas que se hayan guardado; tiene un límite de 32 MB en escritorio. |

El PDF es una edición de lectura, no un archivo certificado para imprenta: incluye títulos, párrafos, negritas y paginación, sin reproducir toda la maquetación de EPUB/DOCX. La fuente incluida no cubre todos los idiomas ni símbolos; si faltan caracteres, la app avisa y permite usar DOCX con otra fuente. No se eliminan caracteres en silencio.

La opción build-novel usa la instalación local descubierta por Codex. Se verificó su presencia, pero no se encontró una licencia de redistribución; no se incluye en los instaladores. Cuando no está instalada, se usa la guía editorial integrada de la app. El registro de cada respuesta indica cuál se usó. Diagnosticar nunca autoriza reescribir.

## Datos y límites

- Desde el código, el trabajo se guarda en `private/workbench/`, excluido de Git; documentos Markdown y metadatos JSON. La app también usa almacenamiento de sesión del navegador para recuperar borradores. Codex guarda su propio historial local en CODEX_HOME. El almacenamiento local no está cifrado por esta app.
- En escritorio, proyectos y sesión Codex se guardan dentro del directorio de datos del usuario de Story Workbench. La sesión es independiente de la del Codex instalado; no se copian credenciales ni proyectos previos. Ver rutas en DESKTOP.md.
- Inferencia online con la cuenta ChatGPT: se envían la petición, las fuentes seleccionadas (incluidas sus sinopsis/POV del plan) y las decisiones del proyecto. Crear un proyecto guiado inicia un turno automáticamente una vez conectada la cuenta; en escritura directa no se llama a Codex hasta enviar una petición. Las respuestas quedan en el historial del proyecto y no se convierten automáticamente en canon ni en un manuscrito. Consume su cuota. Al elegir Codex se fuerza autenticación ChatGPT/proveedor OpenAI, sin claves API ni fallback de pago. Los adaptadores API alternativos se eligen por proyecto y usan su propia clave y facturación; nunca reemplazan a Codex automáticamente. La conversación de voz online usa el proveedor elegido y requiere su propia clave y consentimiento.
- Contexto de fuentes y sus fichas del plan: máximo 60.000 caracteres por envío; decisiones: máximo 30.000 caracteres serializados. Máximo 100 documentos por proyecto y 250 KB UTF-8 por documento. Una tarea IA global a la vez, hasta cuatro minutos; el equipo opcional añade hasta seis minutos para reparto y colaboradores. No son límites de Codex: son límites explícitos de este prototipo.
- Dictado y lectura locales: Vosk 0.3.45 y modelo pequeño español 0.42 incluidos; se carga en memoria al primer dictado. Audio solo en memoria, no se conserva en el proyecto ni se envía a ChatGPT. Solo el texto corregido se envía al pulsar Enviar. La voz sintética y el reconocimiento pueden equivocarse, especialmente con nombres propios. Linux usa eSpeak NG; Windows usa sus voces instaladas. No es el modo de voz de ChatGPT.
- El agente tiene un perfil de lectura limitado a una carpeta vacía, archivos mínimos del sistema y el ejecutable de Codex. Las fuentes viajan como texto, sin conceder acceso a los originales. Shell, hooks, plugins, memorias, conectores configurados, navegador y computer use quedan deshabilitados. La generación nativa de imágenes se permite en entrevista, conversación y borrador sin equipo, únicamente cuando el autor la solicita; diagnósticos y equipos conservan las herramientas deshabilitadas. La captura de micrófono pertenece a la interfaz, no al agente. No hay endpoint genérico para ejecutar comandos.
- El servicio valida Host, Origin y token; rechaza symlinks y rutas fuera del proyecto. Solo un proceso puede abrir un directorio de datos. Es un prototipo de un usuario local, no un servidor público ni una defensa ante procesos maliciosos ejecutados con tu mismo usuario del sistema.
- Las versiones recuperables se guardan antes de reemplazar un archivo. Un cierre abrupto puede dejar una propuesta pendiente aunque el texto ya haya cambiado: la comprobación de hash evita aplicarla otra vez. No editar simultáneamente sus archivos desde otro programa durante un guardado; la comprobación de conflictos no coordina procesos externos ajenos.

Pendientes: edición directa de carpetas externas, importar EPUB/DOCX, exportación KDP/PDF, imágenes generadas, índice de relaciones entre libros/traducciones, evaluación editorial extensa, firma de instaladores y validación nativa Windows/macOS. Repositorio: [radianx/story-workbench](https://github.com/radianx/story-workbench). Los servicios API optativos de voz y los seis adaptadores editoriales experimentales requieren elección explícita; no se hicieron llamadas de pago durante esta entrega.

## Comprobar

Prepará `.venv` con `requirements.txt`. Las pruebas de PDF usan `pdftotext` y `pdfinfo` de **poppler-utils** (`sudo apt-get install poppler-utils` en Ubuntu). Para los recorridos de navegador, instalá Playwright 1.60.0 en ese entorno y Google Chrome; ver [contribución](CONTRIBUTING.md).

```sh
python3 -m unittest discover -s scripts
.venv/bin/python -m unittest discover -s tests
node --check web/app.js
```

Las pruebas HTTP necesitan permisos para abrir sockets de loopback. Node se usa al construir o comprobar el escritorio; los instaladores incluyen lo necesario para ejecutarlo.

```sh
# Navegador: Playwright y Chrome, solo como herramientas de prueba.
.venv/bin/python tests/browser_check.py
.venv/bin/python tests/voice_browser_check.py
.venv/bin/python tests/ux_browser_check.py
.venv/bin/python tests/modes_browser_check.py
.venv/bin/python tests/realtime_browser_check.py
.venv/bin/python tests/gemini_browser_check.py
.venv/bin/python tests/settings_browser_check.py
.venv/bin/python tests/themes_archive_browser_check.py
.venv/bin/python tests/team_chats_browser_check.py
.venv/bin/python tests/motion_browser_check.py
.venv/bin/python tests/setup_browser_check.py
.venv/bin/python tests/providers_browser_check.py
node tests/pcm_playback_check.js
# Motores locales reales; requiere recursos de voz y voz del sistema.
.venv/bin/python tests/live_voice_check.py
# Prueba real con cuota ChatGPT y corpus ficticio temporal.
.venv/bin/python tests/live_mvp.py
# Solo la entrevista real: dos turnos con ficción, sin documentos.
.venv/bin/python tests/live_mvp.py --interview-only
# Modelos y esfuerzos reales; consume cuota ChatGPT con ficción temporal.
.venv/bin/python tests/live_model_check.py
.venv/bin/python tests/live_modes_check.py
```

Ver [resultados del MVP](MVP_RESULTS.md), [prueba inicial del motor](SMOKE_RESULTS.md), [producto](PRODUCT.md), [criterios de implementación](IMPLEMENTATION.md) , [comparación inicial](RESEARCH.md) y [propuesta de mejora aplicada](PRODUCT_IMPROVEMENTS.md).

Ver [pasada de UX y ayuda aplicada en 0.4.0](UX_REVIEW.md).

Ver [modos de traducción y rol](MODES.md) y [voz online, proveedores y condiciones](REALTIME.md), incorporados en 0.5.0.

La 0.7.0 restaura la apariencia antes del primer pintado, comprueba su persistencia entre arranques y añade microinteracciones para acciones pendientes, guardado, tareas, diálogos y controles 3D. Ver [UX](UX_REVIEW.md).

La 0.7.0 añade asistente inicial omisible y reabrible, navegación con Ctrl/Cmd+K y por voz a más secciones, cálculo físico de lomo y [seis motores experimentales](PROVIDERS.md). La voz requiere conexión previa; credenciales, consentimiento y aprobaciones editoriales conservan controles manuales.

Tauri es la única vía de desarrollo y distribución desde 0.8.0. Electron queda retirado; sus resultados anteriores se conservan como historial. Ver [distribución](DESKTOP.md) y [migración y límites de audio](TAURI_MIGRATION.md).

## Estructura para contribuir

- `src/`: servidor HTTP, operaciones editoriales, almacenamiento y adaptadores. Arranque con `python3 -m src.app`.
- `web/`: interfaz sin compilación; la estructura permanente del chat y sus controles está en `index.html`. `bootstrap.js` inicializa los nuevos módulos, `images.js` conserva su estado privado y `formats.js` comparte la importación entre wizard y biblioteca. Los controladores anteriores siguen migrándose gradualmente; no se afirma que todo el frontend sea ya modular.
- `desktop/` y `src-tauri/`: preparación pública de runtimes, integración nativa e instaladores.
- `tests/`: pruebas simuladas de compatibilidad, archivos, seguridad, voz y recorridos de UI.

`project.json` ahora tiene `schema_version`. Los proyectos antiguos se convierten en memoria al leer y se guardan en el formato actual con la próxima modificación; una versión futura desconocida se rechaza sin sobrescribirla. Las aprobaciones, documentos e historiales se conservan. Ver [implementación](IMPLEMENTATION.md) y [contribución](CONTRIBUTING.md).

Las APIs de imágenes siguen los contratos oficiales de [OpenAI Image API](https://developers.openai.com/api/docs/guides/image-generation) y [Gemini](https://ai.google.dev/gemini-api/docs/generate-content/image-generation). Se comprobaron mediante respuestas simuladas; autenticación, disponibilidad y calidad de esas generaciones no se validaron con llamadas facturables. La pantalla de proveedores API sigue siendo experimental. Para generar con la sesión ChatGPT, pedí la imagen directamente en el chat Codex (entrevista, conversación o borrador sin equipo); no necesita una clave API ni cambia automáticamente de proveedor.

### Adjuntos de Codex (código posterior a 0.9.0)

Las imágenes generadas aparecen en el mensaje como miniaturas clickeables. El visor permite ampliar con el control de zoom (o teclas +/−), ajustar a la ventana, descargar el PNG/JPEG original y cerrar con Escape. También funcionan en conversaciones anteriores y en **Imágenes guardadas**. Se conservan automáticamente como adjuntos provisionales del proyecto, incluidos en su ZIP; usarlas como portada sigue requiriendo una decisión del autor.

La integración consume los eventos `imageGeneration` del [protocolo App Server](https://learn.chatgpt.com/docs/app-server), verificados contra el esquema de Codex CLI 0.154.0. Acepta imágenes PNG/JPEG de hasta 15 MB y 20 megapíxeles, con un máximo compartido de 30 imágenes por proyecto. No abre rutas ni imágenes remotas escritas en Markdown. Las miniaturas se cargan desde el servidor local autenticado; los originales se piden al abrir el visor. Si Codex rechaza la generación o devuelve un adjunto incompatible, el chat conserva el texto y muestra el error.

Comprobaciones de este cambio: `python3 -m unittest discover -s tests -p test_codex_images.py` y `python3 tests/codex_images_browser_check.py`. Prueba real con ficción: Codex/ChatGPT produjo un PNG de 1254 × 1254 que quedó adjunto al mensaje, sin clave API. Los instaladores 0.9.0 anteriores todavía no incluyen este cambio.
