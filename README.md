# Story Workbench

Creá, revisá y traducí historias conversando con IA, conservando el control editorial de tu obra.

**[Descargar la última versión instalable](https://github.com/radianx/story-workbench/releases)** · Linux y Windows

## Instalar y empezar

1. En la página de releases, desplegá **Assets** y descargá el instalador de tu sistema:
   - **Linux x64 (Ubuntu 24.04+):** archivo `.deb`.
   - **Windows x64 (Windows 10/11):** archivo `.exe`.
2. Abrí el instalador y seguí sus pasos. Después, abrí **Story Workbench** desde el menú de aplicaciones. No necesitás instalar Python, Codex ni herramientas de programación. Windows puede pedir conexión a internet para instalar WebView2.
3. El asistente inicial te permite elegir el tema, conectar ChatGPT y crear o abrir un proyecto. Podés omitirlo y volver a abrirlo desde **Configuración**.

Para conectar tu cuenta, abrí **ChatGPT → Conectar ChatGPT → Abrir inicio de sesión seguro**, completá el acceso en el navegador y volvé a la app. También podés explorar un proyecto ficticio o trabajar manualmente sin conectar una cuenta.

Los instaladores todavía no están firmados. Para compatibilidad, ubicaciones de datos y detalles de instalación, consultá la [guía de escritorio](docs/DESKTOP.md). macOS aún no tiene instalador.

## Tu primer proyecto

- **Crear una historia:** elegí la creación guiada y contá tu idea. La entrevista avanza una pregunta por vez para definir personajes, mundo, voz y estructura. También podés elegir escritura directa.
- **Continuar una obra:** importá copias de tus archivos Markdown, TXT, EPUB sin DRM o DOCX. Elegí qué fuentes compartir con el asistente y abrí **Ver material** para revisarlas o editarlas.
- **Traducir una obra:** cargá un original y elegí los idiomas de origen y destino. La app puede sugerir el idioma original; vos lo confirmás. La entrevista define intención, registro y criterios antes de preparar una traducción revisable. Al aprobar una unidad, la app prepara el siguiente manuscrito sin traducción según **Plan y avance**; también podés marcar solo otro manuscrito para elegirlo. Si una tarea se interrumpe, podés consultar el texto parcial y usar **Retomar traducción**; el fragmento incompleto no se puede aprobar.

Las importaciones trabajan con copias y dejan los originales en su lugar. EPUB y DOCX se importan como texto: revisá el resultado, porque no se conserva su maquetación ni sus imágenes. **Importar carpeta** permite seleccionar Markdown/TXT de una carpeta y sus subcarpetas.

Al importar una carpeta, queda vinculada inicialmente como destino de traducciones aprobadas. Podés cambiarla o desactivar ese guardado desde **Traducción**. Story Workbench conserva además su copia interna con historial y nunca sobrescribe un archivo externo existente.

En **Configuración → Carpeta de trabajo** podés elegir o crear el espacio donde guardar tus proyectos. El cambio se aplica al reiniciar y no mueve los proyectos existentes.

En **Plan y avance** podés ordenar los capítulos o cuentos. El asistente recibe siempre ese índice, sabe cuál está seleccionado y si ya existe una copia traducida; el texto de los demás documentos solo se envía cuando los marcás como fuente.

## Qué podés hacer

| Función | Cómo te ayuda |
| --- | --- |
| Creación guiada | Desarrollar la historia mediante entrevista, fichas de personajes y mundo, plan de capítulos y borradores que decidís cuándo guardar. |
| Revisión editorial | Pedir diagnósticos, analizar el impacto de un cambio y comparar propuestas antes/después. Solo tu aprobación modifica el texto. |
| Traducción literaria | Acordar un encargo y glosario, resolver matices con citas y alternativas, corregir el borrador y aprobar una copia separada. El acceso **Traducir y consultar matices** junto al chat prepara el siguiente paso sin enviar automáticamente. |
| Biblioteca y conversaciones | Organizar fuentes, buscar contenido, iniciar una conversación con contexto limpio y consultar chats anteriores. El asistente conoce el índice y orden de los manuscritos sin recibir el texto de fuentes no seleccionadas. Archivar retira un proyecto de la biblioteca sin borrar sus archivos. |
| Edición y recuperación | Escribir Markdown con vista previa, deshacer/rehacer y recuperar versiones guardadas desde el historial. |
| Voz | Dictar en español, escuchar respuestas y ajustar el volumen. La voz online opcional conecta el dictado con el mismo chat; también ofrece controles de navegación. |
| Imágenes | Pedir imágenes en el chat Codex y abrir sus miniaturas con zoom, descargar el original o reutilizarlas como portada 3D. Se conservan en el historial y la galería. |
| Libro 3D | Explorar una maqueta giratoria con portada, contraportada, tamaño de hoja y lomo estimado según páginas y papel. El tamaño inicial es 6 × 9 pulgadas. |
| Exportación | Descargar documentos y libros en Markdown, DOCX o PDF de lectura; exportar el proyecto como ZIP con documentos e imágenes guardadas. El ZIP no incluye conversaciones. |
| Personalización | Elegir tema del sistema, paletas claras/oscuras, colores propios, tipografía y opacidad de una imagen de fondo. Las preferencias se recuerdan. |
| Equipo editorial · experimental | Activar «Utilizar múltiples agentes simultáneos» para configurar hasta tres colaboradores, cada uno con su modelo y esfuerzo, en un modal propio. Incluye un panel ciego de lectores simulados. Puede consumir más cuota que un solo agente. |
| Mundos de rol · extra | Preparar personajes, facciones, lugares y reglas para una mesa de rol. No es una plataforma para jugar partidas. |

El PDF y la maqueta 3D sirven para lectura y revisión; no sustituyen la maquetación final ni una prueba de imprenta para KDP. La importación de EPUB no implica exportación a EPUB.

## Usar el chat

Elegí la tarea, el modelo y el esfuerzo debajo del mensaje. El campo crece hasta siete líneas; las respuestas admiten títulos, listas, citas, código y tablas.

Las respuestas nuevas aparecen carácter por carácter a 150 palabras por minuto. En **Configuración → Apariencia e inicio** podés cambiar la velocidad o desactivar el efecto para mostrar cada respuesta inmediatamente.

- **Enter:** enviar. **Shift+Enter:** insertar un salto de línea.
- **Micrófono:** clic para alternar la escucha; mantené Espacio para hablar cuando el mensaje esté vacío.
- **Leer respuestas:** activar o detener la lectura automática.
- **Nueva conversación:** limpiar el chat y el contexto de conversación, conservando fuentes, decisiones y propuestas.
- **Contexto:** el aviso de una línea aparece desde el 85% de la última medición de Codex; podés desactivarlo o cambiar el umbral en Configuración. No incluye el mensaje sin enviar y no aparece sin datos del proveedor.
- **Avisos:** consultar notificaciones y progreso de las tareas.
- **F1:** abrir la ayuda. **Ctrl/Cmd+K:** navegar entre secciones.

## Cuentas y datos

**Codex con ChatGPT es la integración principal.** Usa la disponibilidad y cuota de tu cuenta. Los motores OpenAI API, Gemini, Anthropic, DeepSeek, Kimi y un servidor local son alternativas **experimentales** que elegís explícitamente en Configuración. Los proveedores de voz e imágenes por API también son optativos y pueden tener facturación separada de tu suscripción.

Los proyectos se guardan en tu equipo y sus archivos no se cifran automáticamente. Al usar IA online, la petición y el contexto seleccionado se envían al proveedor elegido; guardar localmente no significa que la inferencia sea privada u offline. En escritorio podés recordar las claves API mediante el almacén seguro del sistema.

La guía editorial integrada permite comenzar sin instalar habilidades adicionales. Si Codex encuentra una instalación local de **build-novel**, la app puede usarla para acompañar la entrevista.

## Más información y contribuciones

[Todas las guías e informes](docs/).

- [Voz, lectura y proveedores](docs/REALTIME.md) · [Motores de IA](docs/PROVIDERS.md)
- [Traducción y rol](docs/MODES.md) · [Temas personalizados](docs/THEMES.md)
- [Instalación y datos locales](docs/DESKTOP.md) · [Seguridad](SECURITY.md)
- [Reportar un problema o sugerir una mejora](https://github.com/radianx/story-workbench/issues)
- [Contribuir y ejecutar desde el código](CONTRIBUTING.md) · [Producto y alcance](docs/PRODUCT.md)

Story Workbench se distribuye bajo la [licencia MIT](LICENSE). Las dependencias conservan sus propias licencias.
