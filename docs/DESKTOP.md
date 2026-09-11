# Distribución Tauri 0.9.2

Tauri es la única vía de escritorio. Los paquetes locales no contienen cuentas, proyectos, conversaciones, imágenes privadas ni habilidades globales. No están publicados ni firmados. El código propio se distribuye bajo la [licencia MIT](../LICENSE); se conservan las licencias de terceros.

## Instalación

- **Linux x64, Ubuntu 24.04+:** abrir `dist/installers/Story-Workbench-0.9.2-linux-amd64.deb` con el instalador gráfico. El paquete `story-workbench` actualiza la instalación anterior y resuelve WebKitGTK, GTK, eSpeak y la apertura del navegador mediante el gestor de paquetes. Otras distribuciones/versiones no están validadas.
- **Windows x64, Windows 10/11:** abrir `Story-Workbench-0.9.2-win-x64.exe`, elegir idioma y seguir el asistente para el usuario actual. Incluye el bootstrapper de WebView2: si falta ese componente, lo instala con internet. Puede aparecer un aviso de editor desconocido. La compilación desde Linux y las pruebas bajo Wine no sustituyen la comprobación en Windows real.
- Abrir **Story Workbench** desde el menú. El asistente inicial empieza por el tema y permite conectar la cuenta propia, configurar voz opcional y crear/abrir un proyecto; se puede omitir y reabrir en Configuración.

Python, Codex CLI 0.153.4, Vosk 0.3.45 y el modelo español pequeño 0.42 vienen incluidos. El usuario no necesita terminal, Node, Rust ni Python. Codex con ChatGPT sigue siendo el motor principal; no hay cambio automático a una API de pago. Los adaptadores con clave son experimentales y requieren elección explícita. No hay actualizaciones automáticas.

## Datos al pasar de Electron

Se conserva el directorio histórico: `~/.config/story-workbench` en Linux (`XDG_CONFIG_HOME` si está definido) y `%APPDATA%/story-workbench` en Windows. `projects` mantiene documentos, conversaciones y decisiones; `codex` mantiene la sesión. El bloqueo del backend impide abrir el mismo perfil simultáneamente desde ambas aplicaciones. Cerrá la app anterior antes de iniciar Tauri. En Linux el .deb actualiza el mismo paquete. En Windows se recomienda desinstalar Electron conservando sus datos antes de instalar Tauri; no se ha validado una actualización automática entre los dos instaladores.

El nuevo perfil web está en `webview`: tema y demás preferencias requieren configurarse una vez. Las claves antiguas de safeStorage permanecen intactas pero Tauri no las convierte; ingresalas una vez para guardarlas en Secret Service (Linux) o Credential Manager (Windows). No hay respaldo en texto plano. La preview 0.8.0-alpha.1 tenía otro perfil, que tampoco se modifica automáticamente.

Configuración → Carpeta de trabajo permite elegir o crear otro espacio de proyectos. La preferencia está en `projects/.workspace.json` del perfil habitual y se aplica al reiniciar. El destino debe estar vacío o identificado por `.story-workbench`; no se reutiliza una carpeta de manuscritos como almacén. No se mueven bibliotecas existentes ni cuentas. Si el destino deja de estar disponible, se abre la biblioteca predeterminada con un aviso; nunca se recrea automáticamente el destino ausente.

Desinstalar conserva los datos. Exportar un proyecto produce un ZIP editorial con documentos y decisiones, sin conversaciones ni imágenes de maqueta; incluye los originales de imágenes generadas que se hayan guardado. Para conservar todo el perfil, usá una copia privada de la carpeta de proyectos. Una copia privada de toda la carpeta `projects` conserva también esos datos; no compartas la carpeta `codex` ni los almacenes de claves.

## Funciones y límites

Conserva los flujos guiados, traducción con criterio humano, construcción de mundos, revisión, historial, temas, selección de motores, voz y libro 3D de 0.7.0. Añade lectura online con modelos TTS OpenAI/Gemini y voz local de respaldo, exportación mediante diálogo nativo y cierre cancelable ante texto sin guardar o una tarea en curso. Las exportaciones se escriben atómicamente en el destino elegido.

**En el WebKitGTK de este Linux no está disponible WebRTC:** la conversación oral OpenAI que usa ese transporte muestra un aviso. La lectura TTS usa HTTP y no tiene esa dependencia; Gemini y el dictado local tienen otro transporte. Las comprobaciones automatizadas usan servicios simulados y micrófono virtual, no validan calidad ni autenticación de proveedores reales. Ver [voz y lectura](REALTIME.md) y [historial técnico](TAURI_MIGRATION.md).

## Reproducir

El flujo mantenido compila ambos paquetes desde Linux x64 con Docker, Node/npm y Python 3.11+. El sidecar Linux de esta entrega usa Python 3.12 de Ubuntu 24.04; no asumir compatibilidad con glibc anterior. Las herramientas son solo para desarrollo:

```sh
npm ci
python3 -m venv .venv
.venv/bin/pip install pyinstaller==6.22.2 -r requirements.txt
docker build -f desktop/tauri-build.Dockerfile -t story-workbench-tauri-build .
npm run dist:linux
npm run dist:win
```

Ejecutar builds secuencialmente: cada preparación reemplaza `src-tauri/runtime`. `desktop/prepare.py` selecciona únicamente fuentes públicas y verifica integridad de las descargas; registra hashes en `MANIFEST.json`. Windows incluye Python embebible oficial 3.14.7 con SHA256 fijado y un lanzador Rust con CRT estático que hereda stdin y espera el cierre de Python; no requiere instalar Visual C++ aparte. NSIS usa zlib para reducir el tiempo de empaquetado. El build de Windows usa cargo-xwin/MSVC y NSIS. Las fuentes de la app y el caché de herramientas son los únicos directorios montados en Docker; no se montan proyectos ni credenciales.

Los instaladores finales y `SHA256SUMS` quedan en `dist/installers`. Los paquetes Electron anteriores son artefactos históricos, no se regeneran. El empaquetado copia `LICENSE` al runtime para incluir el aviso MIT, junto con los avisos de terceros. Los instaladores 0.8.12 generados antes de adoptar MIT no se han reconstruido con ese archivo. build-novel se descubre localmente cuando está instalado, no se copia.

## Comprobaciones ejecutables

```sh
python3 -m unittest discover -s tests
python3 tests/desktop_bridge_check.py
python3 tests/reading_browser_check.py
python3 tests/voice_chat_browser_check.py
python3 tests/reading_browser_check.py --webkit-playback
python3 tests/gemini_browser_check.py --webkit-playback
node tests/pcm_playback_check.js
# Optativo: emite tonos en el dispositivo actual y mide solo la salida de la prueba.
/usr/bin/python3 tests/webkit_audio_output_check.py
# Optativo: mide inicio y continuidad en una salida virtual temporal propia.
/usr/bin/python3 tests/webkit_audio_stream_check.py
cargo test --locked --manifest-path src-tauri/Cargo.toml
# Binario Linux compilado; requiere sesión gráfica y llavero desbloqueado.
python3 tests/tauri_check.py --binary src-tauri/target/release/story-workbench --dialog-tool /usr/bin/xdotool
```

El test nativo usa ficción y claves ficticias en un perfil temporal, dos reinicios, audio virtual y proveedores simulados; borra sus entradas del llavero. El parámetro opcional `--dialog-tool` comprueba selección/cancelación de carpeta e importación de una copia, además de Guardar/Cancelar en el diálogo GTK real, abre el DOCX guardado y verifica una exportación vacía. xdotool y Playwright son herramientas de prueba, no dependencias de la app. La ventana mantiene el sandbox del sistema. Las pruebas nativas de voz pueden modificar el volumen que PipeWire recuerda por rol multimedia en la sesión del usuario; para automatización repetida conviene una sesión de audio aislada. Comprobar el volumen del sistema al terminar.

Referencias: [instaladores NSIS y WebView2](https://v2.tauri.app/distribute/windows-installer/), [paquetes Debian](https://v2.tauri.app/distribute/debian/), [diálogos nativos](https://v2.tauri.app/plugin/dialog/) y [Python embebible](https://docs.python.org/3/using/windows.html#the-embeddable-package). Los resultados efectivamente ejecutados se registran en MVP_RESULTS.md.

Para verificar la integridad del contenido extraído: `python3 tests/installer_check.py --linux-root /tmp/sw-tauri-deb --windows-root /tmp/sw-tauri-nsis`. Los directorios deben contener una extracción fresca del .deb (`dpkg-deb -x`) y del .exe (`7z x`); el test comprueba manifiestos, fuentes públicas, binarios incluidos y SHA256. `tests/windows_sidecar_check.py` comprueba handshake, HTTP y cierre por stdin desde Windows o con `--wine` y un `WINEPREFIX` temporal.

El formato Markdown usa una copia local de [markdown-it 15.0.1](https://github.com/markdown-it/markdown-it), obtenida de su paquete npm oficial. `web/markdown-it.min.js` es el bundle UMD sin modificar; `web/MARKDOWN-IT-LICENSE.txt` incluye su licencia MIT y los avisos de dependencias incluidas. No descarga código ni estilos al abrir la app. Los enlaces HTTP/HTTPS se abren por acción del usuario en el navegador externo; archivos y protocolos ejecutables no se permiten.

En 0.9.0 el runtime incluye ReportLab, Pillow y charset-normalizer con sus metadatos y licencias; Vera incluye su licencia de fuente. El diálogo nativo Guardar acepta también PDF, PNG y JPEG. La API de importación tiene un límite específico de 40 MB por solicitud JSON; el límite general de otros mensajes es de 8 MB para admitir documentos de 1 MB incluso con escapes JSON. Descargas y ZIP permanecen limitados a 32 MB; imágenes individuales a 15 MB.

Para comprobar los cambios de interfaz, módulos y PDF en WebKit sin pruebas de audio ni claves: `.venv/bin/python tests/tauri_check.py --binary src-tauri/target/release/story-workbench --formats-only`.

## Actualización 0.9.2

Añade traducción de capítulos completos, almacenamiento de hasta 1 MB por documento y aviso de contexto configurable. Incluye los adjuntos visuales de Codex y el chat compacto incorporados después de 0.9.0. Los paquetes y hashes están en `dist/installers/`, ignorados por Git.

Verificación de 0.9.2: interfaz en navegador, dos arranques Tauri/WebKit sin pruebas de audio, backend extraído del .deb con PDF/DOCX, dos arranques del sidecar Windows bajo Wine e integridad de ambos instaladores (33 archivos Linux y 458 Windows). Hashes en `SHA256SUMS-0.9.2`; changelog en `RELEASE-0.9.2.md`. Sin prueba de instalación nativa Windows.
