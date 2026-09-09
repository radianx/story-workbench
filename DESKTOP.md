# Distribución de escritorio 0.7.0

Paquetes preliminares locales para probar con otros autores. No se publicaron, no contienen credenciales, proyectos, conversaciones ni habilidades globales. No hay licencia definitiva del producto; `UNLICENSED` evita declarar una licencia inexistente.

## Para el usuario

- **Linux:** paquete `Story-Workbench-0.7.0-linux-amd64.deb`, x64, Ubuntu 24.04 o posterior como base de este build. Abrir con el instalador gráfico, instalar y buscar Story Workbench en el menú. Otras distribuciones/versiones no están validadas. El paquete configura el helper de sandbox/AppArmor mediante los scripts de electron-builder.
- **Windows:** `Story-Workbench-0.7.0-win-x64.exe`, x64. Abrir, elegir instalación para el usuario y seguir el asistente. El paquete está generado desde Linux; falta comprobar instalación y uso en Windows real. El sistema puede mostrar una advertencia de editor desconocido porque todavía no tiene firma.
- **ChatGPT:** Cuenta ChatGPT → Conectar ChatGPT → Abrir inicio de sesión seguro. Usar la cuenta propia en el navegador predeterminado. La app detecta cuando termina el acceso. El editor permanece disponible sin iniciar sesión.

No se comparte la cuenta del creador. El escritorio usa su propio directorio Codex y requiere conectar la cuenta una vez; la versión `python3 app.py` conserva el uso de Codex instalado. La IA editorial usa conexión online y cuota Codex disponible. La voz online opcional usa clave API separada de OpenAI o Gemini, con sus límites y posibles cargos; no usa los beneficios ChatGPT/AI Plus como crédito transferible.

Datos de escritorio: `~/.config/story-workbench/projects` en Linux y `%APPDATA%/story-workbench/projects` en Windows. La carpeta `codex` hermana contiene la sesión administrada por Codex; `voice-keys` contiene solo claves API cifradas cuando se eligió recordarlas. Desinstalar conserva los datos; exportar el proyecto desde la app permite guardar sus documentos y decisiones. El ZIP editorial no incluye conversaciones ni imágenes de maqueta. No compartir la carpeta de sesión.

## Funciones de esta entrega

La 0.7.0 verifica modo y paletas entre arranques y restaura la apariencia antes del primer pintado; añade microinteracciones accesibles en acciones, guardado, tareas, diálogos y maqueta. Conserva el chat amplio, tuerca, seis paletas, micrófono toggle/Espacio y guardado seguro de claves de 0.6.0. Conserva los [modos traducción/rol](MODES.md) y [voz online OpenAI/Gemini](REALTIME.md) de 0.5.0. Incluye la ayuda opcional buscable y mejoras de recuperación, lectura y navegación descritas en [UX_REVIEW.md](UX_REVIEW.md). Mantiene las funciones de 0.3.0: prioriza la entrevista, añade dictado español offline, lectura del sistema, Deshacer/Rehacer, modelo/esfuerzo por proyecto, redacción con guardado explícito, fichas narrativas, plan ordenable, metas y revisión por versión, y exportación del libro a Markdown/DOCX. Ver [propuesta aplicada](PRODUCT_IMPROVEMENTS.md).

Barra por etapas observadas: conexión, contexto, generación y comprobación/guardado. No se inventa un porcentaje del libro ni una duración. Un error o cancelación conserva progreso parcial. Las respuestas nuevas están resaltadas y son colapsables; cada autor puede marcarlas como vistas. Aceptar una propuesta abre su documento y selecciona el texto recién aplicado.

«Libro 3D» abre una maqueta nativa CSS con seis caras: portada, contraportada, lomo y tres cantos de páginas. Se puede girar, inclinar y ajustar ancho, alto y grosor de lomo; importar imágenes para las tres caras impresas y guardar la maqueta por proyecto. Se guardan copias JPEG de vista previa, ajustadas a cada cara, no los originales. No salen hacia Codex. La app no calcula un lomo a partir de palabras ni produce una cubierta técnica para imprenta.

La guía integrada permite empezar sin instalar habilidades. Si Codex descubre build-novel local y está seleccionada, se utiliza esa instalación. No se copia ni distribuye su contenido: no tiene licencia de redistribución declarada en la instalación revisada.

## Reproducir los paquetes

Node 22+, npm, Python 3.11+. Para Linux, construir en Linux con el glibc mínimo que se quiera soportar. El build actual usa Python 3.12 de Ubuntu 24.04; no asumir compatibilidad con glibc anterior. Para generar el `.exe` desde Linux hace falta Wine para las herramientas de recursos/NSIS; eso no equivale a probarlo en Windows.

```sh
npm ci
python3 -m venv .venv
.venv/bin/pip install pyinstaller==6.22.2
npm run dist:linux
npm run dist:win
```

Ejecutar los builds secuencialmente: cada preparación reemplaza `dist/runtime`. Linux empaqueta el servidor mediante PyInstaller. Windows incluye Python embebible oficial 3.14.7 con SHA256 fijado y los módulos de la app. Codex oficial 0.153.4 está incluido en ambos; npm lock/integridad verifican sus paquetes. `MANIFEST.json` registra hashes de los archivos del runtime. Electron y el empaquetador están fijados en package-lock.json. El dictado incluye Vosk 0.3.45 y el modelo español pequeño 0.42, con hashes fijados y avisos de licencia. La preparación descarga estos recursos públicos; el usuario final no tiene que hacerlo. El .deb depende de espeak-ng para leer en español. En Windows la lectura usa las voces del sistema. No hay descarga de ejecutables al iniciar la app ni actualización automática.

El renderer no dispone de Node ni IPC genérico, mantiene aislamiento de contexto y sandbox, restringe navegación y permisos; admite únicamente micrófono de audio desde su ventana principal local, nunca cámara, y solo abre el login oficial en el navegador externo. Un protocolo interno estable conserva preferencias entre arranques; el backend usa un puerto loopback efímero y token. El proceso padre cierra su canal para solicitar la detención del backend y sus trabajos al salir.

## Comprobaciones

```sh
python3 -m unittest discover -s scripts
python3 -m unittest discover -s tests
python3 tests/browser_check.py
python3 tests/ux_browser_check.py
python3 tests/desktop_check.py
# Después de instalar el .deb: sandbox habilitado, datos ficticios temporales.
python3 tests/desktop_check.py --installed --voice
python3 tests/voice_browser_check.py
python3 tests/live_voice_check.py
python3 tests/login_check.py
python3 tests/live_mvp.py --interview-only
```

Las comprobaciones de navegador/escritorio necesitan Chrome/Playwright y permisos de loopback como herramientas de desarrollo, no para usuarios finales. `desktop_check.py` usa `--no-sandbox` **solo en el test desempaquetado**, por las restricciones de namespaces de Ubuntu. La app distribuida no incluye ese flag. El modo `--installed` comprueba el ejecutable instalado con sandbox habilitado. Ver la versión efectivamente instalada y su resultado en MVP_RESULTS.md.

El test de cuenta unitario simula completar el OAuth y verifica que nunca se devuelven tokens ni datos de cuenta. `login_check.py` inicia y cancela un login real en un CODEX_HOME temporal: comprueba protocolo y URL oficial, no la autorización de una cuenta nueva. La entrevista real usa la sesión ChatGPT existente y ficción temporal. Los resultados finales ejecutados se registran en MVP_RESULTS.md.

Referencias de implementación: [seguridad Electron](https://www.electronjs.org/docs/latest/tutorial/security), [distribución Electron](https://www.electronjs.org/docs/latest/tutorial/application-distribution), [App Server de Codex](https://learn.chatgpt.com/docs/app-server), [Python para Windows](https://www.python.org/downloads/windows/) y [empaquetado PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).

Validaciones y límites de cada build: ver el registro de resultados. La instalación actual no se actualiza sin la contraseña administrativa. Ver [resultados](MVP_RESULTS.md).

En 0.7.0 se agrega el asistente inicial, la navegación de secciones, el lomo por páginas y seis motores editoriales experimentales. Sus claves se guardan en `editor-keys`, separadas de `voice-keys`, mediante el mismo almacén nativo. Ver [proveedores](PROVIDERS.md).
