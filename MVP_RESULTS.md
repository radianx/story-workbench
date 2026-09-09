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
