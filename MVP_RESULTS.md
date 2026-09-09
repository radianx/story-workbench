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
