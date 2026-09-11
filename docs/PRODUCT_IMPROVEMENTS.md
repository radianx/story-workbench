# Propuesta de mejora aplicada — versión 0.3.0

Fecha: 2026-09-08. Objetivo: que un autor pueda pasar de una idea a un borrador organizado, revisarlo con control y sacar una copia legible del libro desde una aplicación local. La propuesta de este corte está implementada; las limitaciones al final no se presentan como funciones terminadas.

## Comparación que orientó el corte

Comparación documental de páginas oficiales consultadas en esta fecha. No se ejecutaron versiones comerciales ni se comparó calidad literaria, precisión de revisiones o rendimiento. «No estaba en nuestro MVP» describe la versión 0.2.0, no una carencia atribuida a otros productos.

| Referencia | Función documentada | Nuestro MVP anterior | Evaluación y cambio aplicado |
| --- | --- | --- | --- |
| [Novelcrafter: funciones](https://www.novelcrafter.com/features) | Plan en cuadrícula, etiquetas de escenas, POV y estadísticas del manuscrito. | Biblioteca de documentos sin orden editorial editable ni fichas de escenas. | Aporta orientación durante todo el libro. Plan con tarjetas, orden, sinopsis, POV y estados; cada tarjeta usa el documento real. |
| [Plottr: funciones](https://plottr.com/features/) | Planificación visual de escenas, atributos narrativos y exportación a Word/Scrivener. | Markdown individual o ZIP de fuentes. | Adoptar organización y salida utilizable. Compilación de manuscrito en orden a Markdown y DOCX; controles de subir/bajar accesibles por teclado. No se reproduce su cronología de múltiples tramas. |
| [Sudowrite: Story Bible](https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC) | Personajes, mundo, estilo, esquema y escenas que alimentan la generación. | Roles de fuentes e entrevista; crear fichas exigía empezar de una página vacía. | Fichas propias de personaje, mundo, voz y arco. Empiezan como material provisional sin selección para IA; el autor completa y decide compartir. |
| [Novelcrafter: funciones](https://www.novelcrafter.com/features) | Cambio de modelo durante la conversación y parámetros configurables. | Esfuerzo fijo y modelo predeterminado. | Selector de modelo y esfuerzo por proyecto, basado en el catálogo disponible de la cuenta ChatGPT. Se verifica de nuevo al enviar. |
| Necesidad propia: creación guiada | Convertir la conversación en material editable sin aprobación implícita. | Respuestas y resúmenes; no había una acción específica de redacción. | Modos agrupados Crear/Revisar/Retomar, redacción provisional y guardado explícito en un documento nuevo. Volver a pulsar abre la misma copia. |
| Necesidad propia: avance editorial | Diferenciar actividad del agente de trabajo terminado. | Barra por tarea, palabras del documento activo. | Meta opcional del libro y barra de documentos revisados; solo texto guardado. La marca de revisión se invalida cuando cambia el contenido. |

La documentación confirma que planificación, biblia narrativa, historial, contexto y elección de modelo tienen precedentes. Nuestra hipótesis sigue siendo claridad editorial y trazabilidad de consecuencias con aprobación del autor, usando su sesión ChatGPT. No afirmamos exclusividad ni superioridad demostrada.

## Recorrido resultante

1. **Empezar:** el wizard propone crear conversando por defecto y permite elegir escritura manual. El chat ocupa el centro; «Ver material» abre el panel de documentos cuando hace falta. La entrevista utiliza build-novel instalada o la guía integrada; una pregunta por turno.
2. **Definir:** crear fichas desde «Ficha de historia». Separar ideas de hechos aprobados y registrar las decisiones en su panel. La ficha de voz permite fijar perspectiva, tiempo verbal, registro y recursos a evitar.
3. **Planificar:** «Plan y avance» organiza capítulos o escenas, permite completar sinopsis/POV, reordenar, filtrar por estado y definir una meta. El mismo orden sirve para exportar.
4. **Redactar:** «Preparar con IA» lleva una petición editable al chat; no la envía. Se eligen fuentes, modelo y esfuerzo. «Redactar borrador» produce texto que se guarda únicamente al pulsar el botón correspondiente.
5. **Revisar:** diagnóstico, impacto y propuestas siguen separados. Aceptar un bloque conserva historia y resalta el cambio. «Revisado» es una declaración manual sobre una versión concreta, nunca una conclusión automática de la IA.
6. **Retomar y sacar una copia:** decisiones e historial permanecen; un resumen se guarda como referencia provisional. Descargar el libro en Markdown o DOCX, o el ZIP editorial con fuentes, orden, fichas del plan, meta y decisiones. La maqueta 3D sigue disponible para explorar su aspecto.

## Deshacer y rehacer

Se añadieron botones visibles y se conserva el historial nativo de Chromium para escritura y formato Markdown. Deshacer funciona después de guardar mientras el documento siga abierto. Al cambiar de documento o recargar, las versiones persistidas se recuperan desde Historial; el historial de edición de un documento no debe aparecer en otro. Las aceptaciones del agente se revierten restaurando una versión, sin borrar el registro de la decisión.

## Conversar también con voz

Se aplicó el nuevo énfasis solicitado: entrevista como camino predeterminado, material secundario y respuestas por texto o dictado. El micrófono usa un botón explícito; el audio se procesa localmente y la transcripción se coloca en el mensaje, nunca se envía por sí sola. Capturas de hasta 45 segundos, descarte y cierre de pistas al terminar o cambiar de proyecto.

Para dictado se incluye Vosk 0.3.45 con el modelo pequeño español 0.42. El [catálogo oficial](https://alphacephei.com/vosk/models) identifica ese modelo como Apache 2.0; sus archivos y los motores están fijados por SHA256. La API nativa se usa desde Python estándar, sin servidor de voz ni servicio facturable. El reconocimiento de nombres y frases no es perfecto: la transcripción requiere revisión. El instalador incorpora avisos de terceros.

La lectura genera WAV localmente: eSpeak NG en Linux (dependencia del paquete) y System.Speech con las voces instaladas de Windows. Se puede escuchar una respuesta, detenerla o elegir lectura automática de respuestas nuevas durante el proyecto abierto. La voz Linux es sintética básica; no se promete naturalidad de una voz neural. No se abre el micrófono durante las pruebas reales: se usa una frase generada y, en la prueba de UI, un dispositivo virtual de Chromium.

## Decisión sobre skills

Mantener build-novel unificada. Creación, redacción, revisión y producción son etapas de un mismo proceso editorial; separarlas ahora duplicaría reglas de canon y aprobación sin resolver una necesidad del usuario. Las mejoras de este corte son controles, documentos y persistencia de la aplicación.

Las cuatro plantillas son texto original de esta app. No se copió ni modificó la instalación global de build-novel, que no declara licencia de redistribución. Una skill adicional tendría sentido cuando exista un trabajo editorial repetible y distinto que la guía actual no cubra; este corte no demostró esa necesidad.

## Alcance comprobable y límites

- `tests/test_planning.py`: orden validado, revisiones ligadas al hash, rechazo de estados/textos inválidos, guardado de borrador sin duplicación, presupuesto de contexto, fichas no seleccionadas excluidas, exportación y API.
- `tests/browser_check.py`: uso del plan, meta, ficha, orden, filtros, invalidación tras editar, preparación sin envío, descarga y persistencia, además del recorrido anterior y selección de modelos.
- `tests/voice_browser_check.py`: captura con micrófono virtual, dictado sin envío automático, descarte, rechazo de permisos, reproducción y lectura automática única. `tests/live_voice_check.py` comprueba motores reales con una frase sintética.
- `tests/live_model_check.py`: dos modelos/esfuerzos reales con sesión ChatGPT; continuidad del mismo hilo y ausencia de guardado automático.
- DOCX usa el [formato WordprocessingML documentado por Microsoft](https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document). Es una copia de lectura con títulos, párrafos y saltos entre documentos; otras marcas Markdown se conservan literalmente. No incluye imágenes, comentarios, notas al pie ni maqueta de impresión. La compilación solo incluye fuentes de tipo manuscrito; no mezcla traducciones.
- Un documento es una unidad del plan. Si contiene todo el libro, aparece como una tarjeta. No se divide texto automáticamente ni se impone una estructura de actos.
- La meta mide cantidad y la revisión mide documentos, no calidad literaria ni porcentaje de una novela «terminada». Un cambio de canon en otro archivo todavía requiere solicitar análisis de impacto.
- No se añadieron servicios de pago, colaboración en nube, proveedores alternativos, extracción automática de canon ni generación/publicación de un libro entero. No encajan con el alcance local y el control editorial acordados.
- Linux y Windows mantienen instaladores preliminares. Windows necesita validación nativa; firma, publicación y licencia definitiva requieren su propia decisión. Resultados de paquetes e instalación en [MVP_RESULTS.md](MVP_RESULTS.md).

La evaluación editorial comparativa con tareas idénticas sigue siendo un experimento por ejecutar, descrito en [RESEARCH.md](RESEARCH.md). La comparación documental no lo sustituye.
