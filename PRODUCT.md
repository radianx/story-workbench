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

Primero un autor en su equipo; después pruebas con otros autores usando sus propias cuentas. Sin servicio central que comparta credenciales. Sin generación de libros enteros con un clic, colaboración simultánea, base vectorial o múltiples motores editoriales en la primera versión. La voz admite dos proveedores explícitos y separados del motor editorial. Exportación editorial avanzada para imprenta/EPUB queda fuera de este corte; la exportación DOCX es básica y no redistribuye build-novel.

Archivos locales no significan inferencia offline: el contexto enviado a Codex sale hacia su servicio. Tampoco eliminan el límite de contexto; seleccionamos material pertinente y explicitamos posibles omisiones.

## Corte 0.6.0 aplicado

Configuración en la barra superior; chat y campo de mensaje amplios, micrófono junto a Enviar, clic para alternar escucha y Espacio mientras se mantiene (solo mensaje vacío). Paletas claras celeste/crema/rosado y oscuras violeta/rojo/azul, además de salvia; modo Sistema inicial. Ayuda y voz con modales adaptables, estado de cuenta accesible con punto de color, giro del libro por mouse/teclado. Acepta claves Gemini auth AQ. y permite recordar claves cifradas en el almacén nativo de escritorio; nunca en proyectos ni localStorage.
