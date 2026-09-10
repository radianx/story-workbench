# Personalización, chat y diagnóstico — 0.8.4

- Modelo y esfuerzo junto al tipo de tarea, agrupados bajo el mensaje y adaptables a ventanas angostas. El destino de teclado/voz Modelo lleva al control del chat; los adaptadores experimentales abren su modelo propio.
- Neón y Vice City en ambos modos; paletas personalizadas importables/exportables como JSON validado. Edición inmediata, restitución de salvia y opacidad persistente del ambiente. No se incluyen imágenes en el archivo del tema.
- Prueba explícita de la API de voz con resultado dentro de Configuración: fragmentos, duración, señal, motor y cancelación. El lector local nunca puede enmascarar un fallo de esa prueba.
- Archivar y restaurar retiran proyectos de la biblioteca sin borrar archivos. Un documento sucio o una tarea en curso impiden archivarlo; el último proyecto archivado devuelve a Inicio, desde donde también se puede restaurar.

# Inicio, navegación y producción — 0.7.0

- Primer inicio con tres pasos, omisión explícita/Escape y preferencia persistida. Reapertura en Configuración. Cuenta y voz reutilizan sus controles; no solicitan micrófono al abrir el recorrido.
- Ir a una sección (Ctrl/Cmd+K), búsqueda y Enter; Tab/Shift+Tab nativos, flechas/Home/End en pestañas. Ctrl/Cmd+S no guarda el editor oculto desde un modal. Voz usa destinos explícitos y puede cerrar secciones sin cambios; no obtiene un click arbitrario para aprobar textos.
- Motor editorial separado del proveedor de voz, con etiqueta experimental visible, claves fuera de proyectos y modalidad de guardado clara.
- Libro 3D: 6 × 9 pulgadas, páginas estimadas/reales y papel. Estimación propia de prosa: 300 palabras/página a 6 × 9, márgenes de 15 mm, páginas pares y mínimo visual de 24. Los cambios sin guardar del editor no entran. Lomo: páginas × 0,0572 mm (blanco) o × 0,0635 mm (crema), según [KDP](https://kdp.amazon.com/en_US/help/topic/G201953020). Admite lomo manual y preserva maquetas existentes. No sustituye la paginación ni certifica elegibilidad KDP.

# Microinteracciones y preferencias — 0.6.1

Pasada sobre inicio, configuración, chat, guardado, revisión, voz y maqueta. Movimiento breve, ligado a acciones o estados reales; respeta `prefers-reduced-motion` sin perder información.

| Situación | Cambio y utilidad |
| --- | --- |
| Arranque con un tema elegido | Restaurar modo y paletas antes del primer pintado evita el destello de otra apariencia. Preferencia por usuario local, compartida entre proyectos y conservada al reiniciar Electron. Sistema sigue siendo inicial. |
| Preferencia guardada sin confirmación visible | Configuración explica el guardado automático y su alcance. Prueba explícita de modo oscuro, violeta y rosa entre dos arranques de Electron. |
| Acción pendiente de respuesta | En controles directos, indicador de espera y aria-busy mientras dura la operación; evita repetir ese botón y se libera también ante error. El micrófono mantiene su función de toggle durante la conexión. |
| Apertura de diálogo o paso del wizard | Entrada de 140 ms con desplazamiento de 6 px. Foco y cierre siguen siendo inmediatos; no se demoran acciones para completar animaciones. |
| Guardado | Texto, símbolo y color diferencian borrador de guardado; transición breve, sin anunciar otra vez lo mismo en cada pulsación. |
| Fin de una tarea | Señal breve en el progreso al pasar a completado. Se conserva el elemento de progreso entre actualizaciones; no se reanima la respuesta con cada fragmento recibido. |
| Micrófono | Borde/fondo confirman captura y pausa, conservando etiqueta y estado accesible. Sin pulso continuo decorativo. |
| Libro 3D | Giro suavizado con controles; arrastre directo sin retraso. |

No se añadieron efectos de escritura letra a letra, desplazamiento automático animado, confeti ni transiciones de altura sobre respuestas: perjudicarían lectura, control o estabilidad. Las preferencias no sincronizan entre equipos ni cuentas ChatGPT; pertenecen al usuario local de la app (o perfil/origen del navegador).

# Ajustes de conversación y apariencia — 0.6.0

- Tuerca con ajustes generales, objetivo/flujo, modelo/esfuerzo y voz. El chat conserva espacio y el campo de mensaje tiene borde visible, etiqueta y micrófono junto a Enviar.
- Clic alterna captura; mantener Espacio abre el micrófono y soltarlo lo pausa. No intercepta texto ya escrito, otros formularios ni diálogos. Soltar o perder foco termina la captura iniciada con teclado. Repetición de tecla no agrega espacios. La voz online puede responder con el micrófono pausado.
- Modo Sistema inicial y paletas independientes para claro/oscuro, persistentes. Seis nuevas variantes y salvia original. Botón sol/luna y estado de ChatGPT por color con descripción accesible.
- Modales de configuración/voz de hasta 1100 px y ayuda de hasta 1280 px; columnas adaptables, casillas alineadas, detalles secundarios plegados.
- Arrastre de mouse y flechas para girar/inclinar la maqueta 3D; permanecen los sliders.
- La clave puede recordarse cifrada solo en escritorio con almacén nativo seguro; la configuración informa disponibilidad y no revela la clave recuperada.

# Ayuda y usabilidad — 0.4.0

Pasada sobre los recorridos de la app: inicio, biblioteca, entrevista, edición, revisión, decisiones, plan, voz, cuenta, apariencia, exportación y maqueta. Aplicada el 2026-09-09. Es una inspección con comprobaciones de navegador, no un estudio con usuarios ni una auditoría completa de accesibilidad.

## Cambios aplicados

| Fricción encontrada | Mejora |
| --- | --- |
| Había funciones cuyo funcionamiento solo se explicaba en la documentación del repositorio. | Botón **Ayuda**, disponible desde el inicio y con F1. Once temas desplegables, búsqueda que admite palabras sin tildes, estado sin resultados y limpieza de búsqueda. Todo incluido en la app. |
| Un tour automático interrumpiría la entrevista. | La ayuda se abre únicamente por petición y vuelve al control anterior al cerrar. No crea proyectos, inicia sesión ni envía mensajes; se puede consultar con otro diálogo abierto sin perder su formulario. |
| Los selectores ocupaban espacio de lectura aunque no se estuvieran usando. | **Modelo y esfuerzo** se despliega a petición; su encabezado sigue mostrando la elección actual. Encabezado de entrevista más compacto. |
| No era evidente qué diferencia entrevista, diagnóstico, impacto, propuesta y borrador. | Una explicación breve del tipo de tarea junto al mensaje, con acceso a su ayuda. Describe qué queda provisional y cuándo se modifica un documento. |
| Las explicaciones estaban lejos del punto de uso. | Accesos desde fuentes, tarea, voz, editor, propuestas, decisiones, plan y maqueta. Recordatorios nativos y descripciones accesibles en controles como exportar, ambiente, historial de edición y nueva conversación. Los nombres completos de documentos se pueden consultar con el puntero. |
| Un mensaje aún no enviado desaparecía al recargar y se trasladaba visualmente al cambiar de proyecto. | Conservación del mensaje y su tipo de tarea por proyecto durante la sesión de la ventana. También guarda peticiones preparadas desde el plan y acciones rápidas. Si seguís escribiendo mientras se procesa el envío, ese texto nuevo permanece. |
| Una búsqueda sin coincidencias parecía una biblioteca vacía. | Estados diferentes, botón para limpiar la búsqueda y reinicio del filtro al abrir otro proyecto. |
| Los errores desaparecían antes de poder leerlos o los reemplazaba una notificación de éxito. | Permanecen hasta cerrarlos explícitamente, con rol de alerta. Los éxitos breves conservan su cierre automático. |
| Al actualizar una respuesta, el chat podía saltar mientras se leía otro pasaje. | Desde 0.8.10, por preferencia del usuario, baja al final ante mensajes nuevos o texto nuevo del agente. Ofrece **Ir a la última respuesta** al desplazarse manualmente; otros cambios visuales conservan la posición. |
| Escape podía reutilizar la confirmación anterior del diálogo de nombre. | Cada apertura reinicia su resultado; cancelar ya no puede crear un documento con la confirmación anterior. |
| En ventanas compactas la biblioteca desplazaba la entrevista. | A 600 px o menos, el modo guiado empieza con la biblioteca plegada y ofrece un botón explícito para abrirla. Controles y diálogos se acomodan al ancho disponible; el compositor admite desplazamiento interno en ventanas bajas. |

## Contenido de ayuda

Incluye inicio y entrevista; fuentes y tipos; cuenta, modelo y esfuerzo; dictado y lectura; revisión; decisiones y canon; plan y barras; guardado/deshacer/recuperación; exportación; tema/ambiente/foco/3D; atajos.

Explicita límites que afectan decisiones del autor: seleccionar una fuente no equivale a abrirla, diagnóstico no reescribe, restaurar reemplaza una versión completa, ZIP editorial no es un respaldo íntegro de la app, DOCX es básico y la maqueta no es una cubierta de imprenta. No promete funciones pendientes ni redistribuye build-novel.

## Comprobación reproducible

`python3 tests/ux_browser_check.py` usa proyectos ficticios y una respuesta HTTP simulada. Comprueba apertura voluntaria sin efectos de escritura, búsqueda, Escape/F1/foco, formularios pendientes, recuperación de borradores y aislamiento de mensajes, envío con escritura concurrente, avisos persistentes, cancelación de creación, seguimiento automático de mensajes y biblioteca compacta. Captura la vista a 1440 px y 390 px, incluyendo ayuda oscura. No consume cuota IA ni usa el micrófono.

El recorrido editorial general y el de voz siguen en `tests/browser_check.py` y `tests/voice_browser_check.py`. La prueba empaquetada abre y cierra la ayuda para detectar si falta el nuevo recurso. Resultados efectivamente ejecutados: [MVP_RESULTS.md](MVP_RESULTS.md).

## Límites de esta pasada

Los mensajes sin enviar viven en el almacenamiento de sesión de la ventana: no sustituyen un guardado permanente. No se añadió un tour, analítica de uso ni una biblioteca de tooltips. Quedan por comprobar lectura con tecnologías asistivas reales, uso prolongado con autores nuevos e interfaz/voz en Windows nativo. No se afirma cumplimiento WCAG completo.
