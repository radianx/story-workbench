# Story Workbench

Un espacio local para escribir y revisar historias con IA, conservando el control del autor. Nombre provisional.

**Estado: MVP local ejecutable**, 2026-09-08. Editor, fuentes, conversaciones con Codex y revisión por bloques comprobados con material ficticio. No se modificaron los repositorios de libros.

## Iniciar

Requiere Linux, Python 3.11+ y Codex CLI con sesión ChatGPT para el asistente. La biblioteca y el editor funcionan sin conectar Codex. Sin dependencias de ejecución adicionales ni instalación npm.

```sh
python3 app.py
```

Abrí **el enlace completo que imprime la terminal**: incluye una clave temporal de acceso local en el fragmento. Solo escucha en `127.0.0.1:8765`. Detener con Ctrl+C. Después de reiniciar, abrí el nuevo enlace; los proyectos y las conversaciones siguen guardados. Para otro puerto: `python3 app.py --port 8766`.

Elegí «Explorar un proyecto ficticio» para empezar con cuatro fuentes que contienen una contradicción conocida. O creá un proyecto e importá copias de archivos Markdown/TXT UTF-8. Los originales quedan en su lugar; la app no acepta rutas de libros ni los reorganiza.

## Funciones disponibles

| Área | Qué hace el MVP |
| --- | --- |
| Biblioteca | Varios proyectos, documentos nuevos e importados, búsqueda en nombre y contenido, nombre editable y roles: manuscrito, canon, estilo, referencia, planificación y traducción. |
| Contexto | Selección explícita de fuentes, contador de tamaño, nombres y hashes del material enviado. No recorta fuentes en silencio. Retirar o agregar fuentes abre hilo nuevo para evitar conservar material retirado en el historial del agente. |
| Escritura | Editor Markdown, formato básico, vista previa segura, palabras y tiempo de lectura, atajo Ctrl/Cmd+S, modo foco con Ctrl/Cmd+Shift+F. |
| Recuperación | Borrador por documento en la pestaña, guardado atómico, conflicto ante cambios externos, versiones anteriores y restauración recuperable. |
| Asistente | Cuenta ChatGPT administrada por Codex; conversación, diagnóstico, análisis de impacto hipotético, propuestas y resumen para retomar. Respuesta incremental, detención e hilo persistente por proyecto. |
| Revisión | Antes/después por bloque; aceptar o rechazar. Solo aceptar cambia la copia local. Propuestas desactualizadas fallan sin sobrescribir. |
| Continuidad | Registro manual de decisiones aprobadas, pendientes y rechazadas, registro de aceptaciones, resumen guardable como referencia provisional con fuentes. |
| Apariencia | Tema Sistema por defecto; sigue los cambios claro/oscuro del equipo. También permite elegir Claro u Oscuro y recordar la preferencia en este navegador. |
| Ambiente | Imagen PNG/JPEG/WebP elegida en el equipo, tenue y sin transmisión a Codex. Dura en la pestaña y se retira al cambiar de proyecto. |
| Exportación | Markdown del documento, incluido su borrador; ZIP del proyecto guardado con documentos y manifiesto de nombres, roles y decisiones. No exporta conversaciones. |

La opción build-novel usa la instalación local descubierta por Codex. No la copiamos ni redistribuimos; su licencia sigue pendiente de resolver. Si no está instalada, se puede desmarcar para usar el asistente general. Diagnosticar nunca autoriza reescribir.

## Datos y límites

- Todo el trabajo se guarda en `private/workbench/`, excluido de Git; documentos Markdown y metadatos JSON. La app también usa almacenamiento de sesión del navegador para recuperar borradores. Codex guarda su propio historial local en CODEX_HOME. El almacenamiento local no está cifrado por esta app.
- Inferencia online con la cuenta ChatGPT: se envían la petición, las fuentes seleccionadas y las decisiones del proyecto. Consume su cuota. Se fuerza autenticación ChatGPT/proveedor OpenAI, sin claves API ni fallback de pago.
- Contexto de fuentes: máximo 60.000 caracteres por envío; decisiones: máximo 30.000 caracteres serializados. Máximo 100 documentos por proyecto y 250 KB UTF-8 por documento. Una tarea IA global a la vez, hasta cuatro minutos. No son límites de Codex: son límites explícitos de este prototipo.
- El agente tiene un perfil de lectura limitado a una carpeta vacía, archivos mínimos del sistema y el ejecutable de Codex. Las fuentes viajan como texto, sin conceder acceso a los originales. Shell, hooks, plugins, memorias, conectores configurados, navegador, computer use e imágenes quedan deshabilitados para estos trabajos. No hay endpoint genérico para ejecutar comandos.
- El servicio valida Host, Origin y token; rechaza symlinks y rutas fuera del proyecto. Solo un proceso puede abrir un directorio de datos. Es un prototipo de un usuario local, no un servidor público ni una defensa ante procesos maliciosos ejecutados con tu mismo usuario del sistema.
- Las versiones recuperables se guardan antes de reemplazar un archivo. Un cierre abrupto puede dejar una propuesta pendiente aunque el texto ya haya cambiado: la comprobación de hash evita aplicarla otra vez. No editar simultáneamente sus archivos desde otro programa durante un guardado; la comprobación de conflictos no coordina procesos externos ajenos.

Pendientes: edición directa de carpetas externas, importar EPUB/DOCX, exportación KDP/PDF, imágenes generadas, índice de relaciones entre libros/traducciones, evaluación editorial extensa, distribución y licencia. No hay remoto, publicación ni servicios de pago.

## Comprobar

```sh
python3 -m unittest discover -s scripts
python3 -m unittest discover -s tests
node --check web/app.js
```

Las pruebas HTTP necesitan permisos para abrir sockets de loopback. Node solo se usa en la comprobación opcional de sintaxis; no es necesario para ejecutar la app.

```sh
# Navegador: Playwright y Chrome, solo como herramientas de prueba.
python3 tests/browser_check.py
# Prueba real con cuota ChatGPT y corpus ficticio temporal.
python3 tests/live_mvp.py
```

Ver [resultados del MVP](MVP_RESULTS.md), [prueba inicial del motor](SMOKE_RESULTS.md), [producto](PRODUCT.md), [criterios de implementación](IMPLEMENTATION.md) y [comparación inicial](RESEARCH.md).
