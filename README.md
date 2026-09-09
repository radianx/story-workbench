# Story Workbench

Un espacio local para escribir y revisar historias con IA, conservando el control del autor. Nombre provisional.

**Estado: MVP de escritorio 0.3.0**, 2026-09-08. Editor, fuentes, conversaciones con Codex y revisión por bloques comprobados con material ficticio. No se modificaron los repositorios de libros.

## Instalar la app de escritorio

Los paquetes locales están en `dist/installers/`. Ver [distribución y comprobaciones](DESKTOP.md) para los límites de validación de cada sistema.

1. **Linux x64 (Ubuntu 24.04+):** abrí el archivo `.deb` con el instalador de aplicaciones del sistema e instalalo. **Windows x64:** abrí el `.exe` y seguí el asistente de instalación.
2. Abrí **Story Workbench** desde el menú de aplicaciones.
3. Elegí **Cuenta ChatGPT → Conectar ChatGPT → Abrir inicio de sesión seguro**. Completá el acceso en tu navegador y volvé a la app.

Incluye Electron, Python y Codex: el usuario no necesita terminal ni instalarlos por separado. Cada instalación usa la cuenta del autor que la abre. Se puede escribir sin iniciar sesión; la IA necesita internet y disponibilidad de Codex en esa cuenta. No admite claves API ni fallback de pago. Los paquetes son preliminares y no están firmados ni publicados.

## Iniciar desde el código

Requiere Python 3.11+ y Codex CLI con sesión ChatGPT para el asistente. La biblioteca y el editor funcionan sin conectar Codex. El servidor usa biblioteca estándar de Python. El dictado necesita los recursos nativos de voz preparados al construir el escritorio; en Linux, la lectura usa espeak-ng (el .deb lo instala como dependencia).

```sh
python3 app.py
```

Para preparar el dictado al ejecutar desde código: `python3 desktop/prepare_voice.py --target linux` (descarga recursos públicos). La instalación `.deb` ya incluye el modelo y resuelve la dependencia de lectura del sistema.

Abrí **el enlace completo que imprime la terminal**: incluye una clave temporal de acceso local en el fragmento. Solo escucha en `127.0.0.1:8765`. Detener con Ctrl+C. Después de reiniciar, abrí el nuevo enlace; los proyectos y las conversaciones siguen guardados. Para otro puerto: `python3 app.py --port 8766`.

Elegí «Explorar un proyecto ficticio» para empezar con cuatro fuentes que contienen una contradicción conocida. O creá un proyecto: el asistente inicial pide un nombre, cómo querés continuar y una idea opcional. «Escribir por mi cuenta» abre un manuscrito en blanco. «Crear conversando», opción predeterminada, pone el chat en el centro, permite abrir el material con «Ver material» e inicia una entrevista editorial (usa build-novel si está instalada), una pregunta por vez, incluso sin documentos. También podés importar copias de archivos Markdown/TXT UTF-8. Los originales quedan en su lugar; la app no acepta rutas de libros ni los reorganiza.

## Funciones disponibles

| Área | Qué hace el MVP |
| --- | --- |
| Inicio guiado | Wizard de dos pasos con entrevista como opción predeterminada; escritura directa o entrevista editorial con build-novel local o la guía integrada. La forma de trabajo se guarda por proyecto y se puede cambiar desde la biblioteca. Recargar no duplica la bienvenida; una entrevista fallida o interrumpida puede retomarse. |
| Biblioteca | Varios proyectos, documentos nuevos e importados, búsqueda en nombre y contenido, nombre editable y roles: manuscrito, canon, estilo, referencia, planificación y traducción. |
| Contexto | Selección explícita de fuentes, contador de tamaño, nombres y hashes del material enviado. No recorta fuentes en silencio. Retirar o agregar fuentes abre hilo nuevo para evitar conservar material retirado en el historial del agente. |
| Escritura | Editor Markdown, formato básico, vista previa segura, palabras y tiempo de lectura, atajo Ctrl/Cmd+S, modo foco con Ctrl/Cmd+Shift+F, botones Deshacer/Rehacer y atajos Ctrl+Z/Ctrl+Shift+Z (Cmd en macOS). Texto y formato usan el historial nativo del editor; al cambiar de documento o recargar, recurrir a Historial para las versiones guardadas. |
| Recuperación | Borrador por documento en la pestaña, guardado atómico, conflicto ante cambios externos, versiones anteriores y restauración recuperable. |
| Asistente | Cuenta ChatGPT administrada por Codex; conversación, diagnóstico, análisis de impacto hipotético, propuestas y resumen para retomar. Respuesta incremental, detención e hilo persistente por proyecto. |
| Plan y avance | Tarjetas de capítulos o escenas sobre los manuscritos, sinopsis, POV, orden y filtro por estado; meta de palabras y progreso de revisión. Cambiar un texto revisado invalida esa marca. |
| Fichas | Plantillas propias de personaje, mundo, voz y arco; documentos provisionales inicialmente sin seleccionar para IA. |
| Voz | Dictado local en español, hasta 45 segundos por captura, transcripción editable antes de enviar, descarte y apagado del micrófono al cambiar de proyecto. Lectura local de respuestas, detención y lectura automática opcional de respuestas nuevas. |
| Modelos | Catálogo de la cuenta ChatGPT y esfuerzos compatibles; selección por proyecto, comprobación al enviar y modelo/esfuerzo efectivo en cada respuesta. |
| Creación | Redacción guiada y botón explícito para guardar como nuevo borrador provisional; repetirlo abre la misma copia. |
| Seguimiento | Barra de cuatro etapas reales por tarea, sin estimar el porcentaje del libro. Respuestas colapsables con resaltado Nuevo y Marcar como visto; conserva estado al recargar. |
| Libro 3D | Maqueta giratoria de portada, lomo, contraportada y páginas. Medidas en milímetros, título, autor e imágenes locales guardadas por proyecto. Es visual, no un archivo listo para imprenta. |
| Revisión | Antes/después por bloque; aceptar o rechazar. Solo aceptar cambia la copia local y selecciona el texto resultante en el editor. Propuestas desactualizadas fallan sin sobrescribir. |
| Continuidad | Registro manual de decisiones aprobadas, pendientes y rechazadas, registro de aceptaciones, resumen guardable como referencia provisional con fuentes. |
| Apariencia | Tema Sistema por defecto; sigue los cambios claro/oscuro del equipo. También permite elegir Claro u Oscuro y recordar la preferencia en este navegador. |
| Ambiente | Imagen PNG/JPEG/WebP elegida en el equipo, tenue y sin transmisión a Codex. Dura en la pestaña y se retira al cambiar de proyecto. |
| Exportación | Markdown del documento, incluido su borrador; ZIP del proyecto guardado con documentos y manifiesto de nombres, roles y decisiones. No exporta conversaciones. Desde Plan y avance: libro completo en orden a Markdown y DOCX básico de lectura. |

La opción build-novel usa la instalación local descubierta por Codex. Se verificó su presencia, pero no se encontró una licencia de redistribución; no se incluye en los instaladores. Cuando no está instalada, se usa la guía editorial integrada de la app. El registro de cada respuesta indica cuál se usó. Diagnosticar nunca autoriza reescribir.

## Datos y límites

- Desde el código, el trabajo se guarda en `private/workbench/`, excluido de Git; documentos Markdown y metadatos JSON. La app también usa almacenamiento de sesión del navegador para recuperar borradores. Codex guarda su propio historial local en CODEX_HOME. El almacenamiento local no está cifrado por esta app.
- En escritorio, proyectos y sesión Codex se guardan dentro del directorio de datos del usuario de Story Workbench. La sesión es independiente de la del Codex instalado; no se copian credenciales ni proyectos previos. Ver rutas en DESKTOP.md.
- Inferencia online con la cuenta ChatGPT: se envían la petición, las fuentes seleccionadas (incluidas sus sinopsis/POV del plan) y las decisiones del proyecto. Crear un proyecto guiado inicia un turno automáticamente una vez conectada la cuenta; en escritura directa no se llama a Codex hasta enviar una petición. Las respuestas quedan en el historial del proyecto y no se convierten automáticamente en canon ni en un manuscrito. Consume su cuota. Se fuerza autenticación ChatGPT/proveedor OpenAI, sin claves API ni fallback de pago.
- Contexto de fuentes y sus fichas del plan: máximo 60.000 caracteres por envío; decisiones: máximo 30.000 caracteres serializados. Máximo 100 documentos por proyecto y 250 KB UTF-8 por documento. Una tarea IA global a la vez, hasta cuatro minutos. No son límites de Codex: son límites explícitos de este prototipo.
- Voz: Vosk 0.3.45 y modelo pequeño español 0.42 incluidos; se carga en memoria al primer dictado. Audio solo en memoria, no se conserva en el proyecto ni se envía a ChatGPT. Solo el texto corregido se envía al pulsar Enviar. La voz sintética y el reconocimiento pueden equivocarse, especialmente con nombres propios. Linux usa eSpeak NG; Windows usa sus voces instaladas. No es el modo de voz de ChatGPT.
- El agente tiene un perfil de lectura limitado a una carpeta vacía, archivos mínimos del sistema y el ejecutable de Codex. Las fuentes viajan como texto, sin conceder acceso a los originales. Shell, hooks, plugins, memorias, conectores configurados, navegador, computer use e imágenes quedan deshabilitados para estos trabajos. La captura de micrófono pertenece a la interfaz, no al agente. No hay endpoint genérico para ejecutar comandos.
- El servicio valida Host, Origin y token; rechaza symlinks y rutas fuera del proyecto. Solo un proceso puede abrir un directorio de datos. Es un prototipo de un usuario local, no un servidor público ni una defensa ante procesos maliciosos ejecutados con tu mismo usuario del sistema.
- Las versiones recuperables se guardan antes de reemplazar un archivo. Un cierre abrupto puede dejar una propuesta pendiente aunque el texto ya haya cambiado: la comprobación de hash evita aplicarla otra vez. No editar simultáneamente sus archivos desde otro programa durante un guardado; la comprobación de conflictos no coordina procesos externos ajenos.

Pendientes: edición directa de carpetas externas, importar EPUB/DOCX, exportación KDP/PDF, imágenes generadas, índice de relaciones entre libros/traducciones, evaluación editorial extensa, firma de instaladores, validación nativa Windows/macOS y licencia definitiva. No hay remoto, publicación ni servicios de pago.

## Comprobar

```sh
python3 -m unittest discover -s scripts
python3 -m unittest discover -s tests
node --check web/app.js
```

Las pruebas HTTP necesitan permisos para abrir sockets de loopback. Node se usa al construir o comprobar el escritorio; los instaladores incluyen lo necesario para ejecutarlo.

```sh
# Navegador: Playwright y Chrome, solo como herramientas de prueba.
python3 tests/browser_check.py
python3 tests/voice_browser_check.py
# Motores locales reales; requiere recursos de voz y voz del sistema.
python3 tests/live_voice_check.py
# Prueba real con cuota ChatGPT y corpus ficticio temporal.
python3 tests/live_mvp.py
# Solo la entrevista real: dos turnos con ficción, sin documentos.
python3 tests/live_mvp.py --interview-only
# Modelos y esfuerzos reales; consume cuota ChatGPT con ficción temporal.
python3 tests/live_model_check.py
```

Ver [resultados del MVP](MVP_RESULTS.md), [prueba inicial del motor](SMOKE_RESULTS.md), [producto](PRODUCT.md), [criterios de implementación](IMPLEMENTATION.md) , [comparación inicial](RESEARCH.md) y [propuesta de mejora aplicada](PRODUCT_IMPROVEMENTS.md).
