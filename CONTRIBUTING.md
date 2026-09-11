# Contribuir a Story Workbench

Se pueden proponer mejoras, reportar errores, probar Linux/Windows, revisar accesibilidad o aportar código y documentación. Issues y pull requests pueden estar en español o inglés. No hace falta una cuenta de IA para trabajar en la interfaz, el almacenamiento o las pruebas simuladas.

El código propio del proyecto y sus contribuciones se distribuyen bajo la [licencia MIT](LICENSE). No se exige cesión de derechos. Conservá el aviso de copyright y los avisos de terceros, que mantienen sus propias licencias.

## Primer arranque

1. Creá un fork de [radianx/story-workbench](https://github.com/radianx/story-workbench), cloná tu fork y entrá en la carpeta del repositorio.
2. Leé [README.md](README.md), [docs/PRODUCT.md](docs/PRODUCT.md) y [AGENTS.md](AGENTS.md). README describe el estado actual; los cortes antiguos de producto y resultados son históricos.
3. Con Python 3.11 o posterior, ejecutá desde la raíz:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python -m src.app --data-dir private/contrib --port 8766
   ```

4. Abrí el enlace completo que imprime la terminal. Su token es temporal y privado. Omití conectar cuentas y elegí «Explorar un proyecto ficticio». Detené el servidor con Ctrl+C.

El backend usa la biblioteca estándar de Python, con ReportLab/Pillow para PDF e imágenes y la interfaz es HTML/CSS/JavaScript sin compilación. Para este recorrido no hacen falta npm, Rust, Docker, Codex ni claves. Los cambios web se ven al recargar; los cambios Python requieren reiniciar. `private/` está excluido de Git. Usá datos inventados, incluso para capturas y errores.

En Windows, si tu instalación ofrece `py` en lugar de `python3`, usá `py -3`. El recorrido automatizado de navegador descrito abajo está preparado para Linux; no equivale a una comprobación nativa de Windows.

Las guías de uso, arquitectura y los informes técnicos están en [`docs/`](docs/).

## Dónde cambiar cada cosa

| Área | Entrada en el código | Comprobación relacionada |
| --- | --- | --- |
| Servidor HTTP y controles de acceso | `src/app.py` | `tests/test_workbench.py` |
| Importación, PDF, imágenes y migraciones | `src/workbench_import.py`, `src/workbench_pdf.py`, `src/workbench_images.py`, `src/workbench_migrations.py`, `web/images.js` | `tests/test_formats.py`, `tests/test_images.py`, `tests/formats_browser_check.py` |
| Documentos, versiones, biblioteca y workspace | `src/workbench_store.py`, `src/workbench_workspace.py` | `tests/test_workbench.py`, `tests/test_workspace.py` |
| Codex, cuenta y equipo editorial | `src/workbench_ai.py`, `src/workbench_account.py`, `src/workbench_team.py`, `scripts/codex_smoke.py` | `scripts/test_codex_smoke.py`, `tests/test_team.py` |
| Proveedores experimentales | `src/workbench_providers.py`, `web/providers.js` | `tests/test_providers.py`, `tests/providers_browser_check.py` |
| Chat, formato, ajustes y temas | `web/index.html`, `web/style.css`, `web/app.js`, `web/markdown.js`, `web/settings.js`, `web/appearance.js` | `tests/ux_browser_check.py`, `tests/markdown_browser_check.py`, `tests/themes_archive_browser_check.py` |
| Traducción y rol | `src/workbench_modes.py`, `web/modes.js` | `tests/test_modes.py`, `tests/modes_browser_check.py` |
| Voz y lectura | `src/workbench_voice.py`, `src/workbench_realtime.py`, `web/voice.js`, `web/realtime.js`, `web/gemini-voice.js` | `tests/test_voice.py`, `tests/test_realtime.py`, `tests/pcm_playback_check.js` |
| Ventana nativa, llavero y procesos | `src-tauri/src/`, `desktop/sidecar/` | [docs/DESKTOP.md](docs/DESKTOP.md#comprobaciones-ejecutables) |
| Instaladores | `desktop/prepare.py`, `desktop/build.py` | `tests/installer_check.py` |

La interfaz habla con el servidor Python local. Rust es la envoltura Tauri y sus capacidades nativas; no reemplaza al backend editorial. El servidor coordina el proveedor elegido y conserva las aprobaciones del autor.

## Comprobar un cambio

Desde la raíz, con Python 3.11+ y Node.js 22, estas comprobaciones no necesitan claves ni recursos de voz:

```sh
python3 -m unittest discover -s scripts
.venv/bin/python -m unittest discover -s tests
node tests/pcm_playback_check.js
```

Para los archivos JavaScript modificados: `node --check web/app.js` (sustituí la ruta). El CI comprueba la sintaxis de todos los JavaScript de `web/` y `tests/`. Los tests HTTP abren sockets en loopback y usan directorios temporales. Las pruebas de equipo sustituyen App Server por un doble y usan el ejecutable de Python como referencia para construir los permisos: no requieren encontrar Codex ni ejecutan ese proceso.

Para cambios de interfaz, instalá Playwright en un entorno de desarrollo y Google Chrome en Linux, donde los recorridos actuales buscan `/usr/bin/google-chrome`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt playwright==1.60.0
# Para verificar texto y páginas de PDF en Linux: instalar poppler-utils.
.venv/bin/python tests/ux_browser_check.py
.venv/bin/python tests/modes_browser_check.py
.venv/bin/python tests/markdown_browser_check.py
.venv/bin/python tests/formats_browser_check.py
.venv/bin/python tests/codex_images_browser_check.py
```

Instalar solo el Chromium de Playwright no satisface esa ruta. El CI verifica Chrome antes de ejecutar esos cinco recorridos. No usan proveedores reales; otros recorridos por área están en `tests/` y en [esta sección](#comprobar-un-cambio).

Las pruebas `live_*` son optativas: algunas usan cuentas, cuota o APIs facturables. Leé su encabezado y configuración antes de ejecutarlas. No forman parte del CI. Las pruebas nativas de audio requieren sesión gráfica/dispositivos y pueden afectar el volumen del sistema: sus requisitos están en [docs/DESKTOP.md](docs/DESKTOP.md). No necesitás construir instaladores para un cambio de documentación o web; si tocás escritorio o empaquetado, seguí ese documento y ejecutá las builds secuencialmente.

## Un pull request fácil de revisar

1. Buscá un issue existente. Para una función grande o un cambio de formato de proyectos, describí primero el problema, la propuesta y cómo conservar los datos existentes. Una corrección pequeña puede ir directamente a un PR.
2. Creá una rama con un nombre descriptivo y mantené el cambio acotado. Reutilizá componentes y pruebas existentes; no hace falta una nueva dependencia para una mejora pequeña.
3. Agregá una comprobación ejecutable para lógica no trivial. Para UI, verificá teclado, foco, tema y ventana compacta cuando corresponda. Los cambios solo de documentación no necesitan tests nuevos.
4. Explicá el comportamiento anterior y el nuevo, los comandos ejecutados y cualquier limitación. Indicá expresamente qué no pudiste probar. Un PR en borrador sirve para recibir comentarios tempranos.
5. Revisá `git diff --cached` antes del commit. No incluyas libros, chats, claves, perfiles, tokens de enlaces locales, audio privado ni instaladores. No cambies la versión de la app salvo que el cambio sea una entrega acordada.

La IA puede ayudar a contribuir; quien presenta el PR debe entenderlo y verificarlo. No publiques prompts o respuestas con material privado como evidencia. Las propuestas editoriales siguen requiriendo aceptación humana, y los adaptadores experimentales no sustituyen a Codex automáticamente.

Tratemos las preguntas con respeto, expliquemos los desacuerdos y critiquemos el cambio, no a la persona. Acoso, insultos y divulgación de datos privados no son aceptables; el mantenedor puede moderar comentarios o cerrar contribuciones que incumplan estas pautas. Para vulnerabilidades, usá [SECURITY.md](SECURITY.md).

## Buenos primeros aportes

Estas son áreas candidatas, no issues ya asignados ni funciones prometidas:

- Mejorar un texto de ayuda o un tooltip a partir de una confusión reproducible.
- Corregir un problema concreto de contraste, teclado o foco en un tema.
- Compartir un tema JSON con una vista previa ficticia: ver [docs/THEMES.md](docs/THEMES.md).
- Probar instalación y actualización en Windows real, documentando versión y pasos.
- Reducir un bug a un ejemplo ficticio y añadirlo a la comprobación existente.

Las funciones grandes pendientes se describen en [docs/PRODUCT.md](docs/PRODUCT.md); conviene acordar un corte pequeño antes de implementarlas.

## Al abrir el repositorio en GitHub — mantenedor

- Conservar la licencia MIT del código propio y verificar por separado avisos y permisos de dependencias; build-novel no se distribuye.
- Revisar los archivos y el historial que se publicarán, no solo el estado actual. `.gitignore` no elimina contenido de commits anteriores. `docs/HANDOFF.md`, `private/` y `dist/` son locales.
- Activar el canal **Security → Report a vulnerability** y probar que está disponible. [Configuración oficial](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
- Ejecutar el workflow **Checks** en GitHub. Después de su primera ejecución, configurar las comprobaciones requeridas para PR en la rama principal según las opciones de la cuenta. El workflow por sí solo no configura protección de ramas.
- Crear unos pocos issues concretos con criterio de aceptación; reservar `good first issue` para tareas pequeñas con ubicación y forma de comprobarlas. `help wanted` puede indicar pruebas de plataforma o revisión editorial.

El workflow no publica paquetes ni usa cuentas de autores. Su ejecución en GitHub y las opciones anteriores deben verificarse después de subir el workflow al remoto. Las [guías de contribución](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) y las [recomendaciones de seguridad para Actions](https://docs.github.com/en/actions/reference/security/secure-use) explican las convenciones utilizadas.

## Límites del código

`src/app.py` valida el transporte, el origen y la autenticación; `src/workbench_operations.py` ejecuta operaciones del proyecto sin depender del handler HTTP. Las claves no entran en `Store`. Las conversiones de formato operan sobre copias y las migraciones de JSON no escriben al leer. No agregues archivos Python de aplicación en la raíz.

El chat y los controles permanentes se declaran en HTML. La nueva funcionalidad web usa módulos con dependencias explícitas e inicialización desde `bootstrap.js`; cada controlador conserva su propio estado. El puente con los controladores clásicos está concentrado allí. `formats.js` no depende del estado del chat. Para migrar otro controlador, preservá sus recorridos de UI y evitá introducir un segundo propietario de su estado.

Validación adicional del workflow: `actionlint .github/workflows/checks.yml`. `runner` no está disponible en el `env` del job; el perfil temporal de pruebas se prepara en un paso con `RUNNER_TEMP` y `GITHUB_ENV`.
