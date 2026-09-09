# Migración a Tauri

La entrega utilizable sigue siendo Electron 0.7.0 (`2e9236f`). Los instaladores Linux y Windows permanecen en `dist/installers/`, con SHA256. Tauri está en `src-tauri/` como vista previa 0.8.0-alpha.1; no sustituye ni importa automáticamente la instalación existente.

## Pistas verificadas

- **Sidecars:** el plugin oficial Shell permite iniciar el backend desde Rust sin conceder ejecución de comandos al frontend. `externalBin` empaqueta binarios que ya preparamos para cada arquitectura; no los compila ni convierte automáticamente. [Documentación](https://v2.tauri.app/develop/sidecar/).
- **Claves:** Stronghold cifra datos pero necesita una contraseña/clave maestra y su derivación; no es un reemplazo transparente del llavero. Evitar una contraseña adicional requiere resolver el secreto maestro o usar el almacén nativo mediante Rust. [Stronghold](https://v2.tauri.app/plugin/stronghold/) y [keyring](https://docs.rs/keyring/3.6.3/keyring/). Electron actual usa safeStorage, no keytar.
- **Archivos:** el plugin FS admite scopes explícitos. Aquí los archivos ya pasan por Python con validación de rutas, hashes y bloqueo; conservar esa frontera permite no instalar FS ni otorgar acceso al disco al frontend. Los scopes del plugin no limitan por sí solos el código Rust/Python. [FS](https://v2.tauri.app/plugin/file-system/).
- **Motor web:** Linux usa WebKitGTK y Windows WebView2. La voz necesita comprobación propia, especialmente contexto seguro, permiso de micrófono, AudioWorklet y WebRTC. [Motores web](https://v2.tauri.app/reference/webview-versions/).

## Implementación inicial

- Backend Python empaquetado como ejecutable sidecar nativo de un archivo; Codex y voz reutilizan recursos públicos de la build verificada. No se redistribuyen cuentas, claves ni skills globales.
- Ventana Tauri con la misma interfaz y origen estable. Proxy exclusivamente al servidor de loopback surgido del handshake validado; mantiene token, Host/Origin, límites de tamaño y CSP del backend. No permite un destino de red arbitrario.
- Plugin Shell usado desde Rust; capacidades del frontend vacías. Solo enlaces OAuth del dominio permitido pueden abrir el navegador externo.
- Datos y perfil de la vista previa separados. Claves opcionales en el llavero nativo mediante keyring 3.6.3: Secret Service con transporte cifrado en Linux y Credential Manager en Windows (implementado, todavía sin prueba Windows). Voz y motores editoriales usan entradas separadas por proveedor y perfil. No intenta leer ni convertir los archivos cifrados de Electron; no hay fallback a archivos de texto.
- Se conservan ambos shells durante la transición. Antes de cambiar el producto distribuido faltan: migración recuperable de preferencias/proyectos/claves de Electron, paridad de voz online y comprobación Windows, cierre de tareas y descarga con diálogo nativo, instaladores Tauri y regresiones completas.

## Preparar y comprobar

Primero generar y verificar la build Electron del sistema nativo; luego:

```sh
python3 desktop/prepare_tauri.py
cargo test --manifest-path src-tauri/Cargo.toml
cargo build --manifest-path src-tauri/Cargo.toml
python3 tests/tauri_check.py
```

Rust y las dependencias de GTK pueden instalarse en una imagen aislada mediante `desktop/tauri-build.Dockerfile`. Montar únicamente `src-tauri`, `web` de solo lectura y un caché de Cargo; no montar proyectos ni credenciales. El helper prepara Linux o Windows x64 desde su propio sistema; no genera un sidecar Windows con el Python Linux.

La prueba de ventana usa un directorio temporal, ficción, claves ficticias y el micrófono virtual de WebKit; no usa cuentas, servicios de pago ni el micrófono físico. Limpia sus propias entradas del llavero incluso ante fallos. Un llavero inaccesible hace fallar esta comprobación de persistencia; no se registra como aprobada. No prueba todo el producto ni autoriza declarar paridad con Electron. Los resultados observados se registran al completar la ejecución.

## Resultados observados — 2026-09-09

- Imagen aislada Rust 1.98.1/GTK de Debian; base fijada por digest y dependencias Rust fijadas en Cargo.lock. Compilación y prueba Rust de handshake/orígenes aprobadas.
- Sidecar Linux generado con PyInstaller y recursos verificados de Electron 0.7.0. Binario Tauri arrancado en este Linux con WebKitGTK del sistema, sin desactivar su sandbox.
- Dos arranques consecutivos sobre el mismo directorio temporal pasaron: proyecto ficticio, editor, navegación, tema recordado, 6 × 9 en libro 3D y descarga HTTP de DOCX. Sin sesión ChatGPT ni llamadas API.
- La primera comprobación de reinicio falló porque matar el lanzador no esperaba la liberación de Python. Se reemplazó por cierre de stdin y espera acotada de la salida del proceso. La repetición de ambos arranques pasó; el caso queda cubierto por `tests/tauri_check.py`.
- El DOCX se comprobó por HTTP; el diálogo de descarga/guardado del sistema sigue pendiente. La migración de datos/perfil/claves de Electron, Windows y los instaladores Tauri siguen pendientes.

## Segundo tramo — llavero y voz, 2026-09-09

- Guardar, recordar sin volver a ingresar, recuperar al arrancar y olvidar claves de voz y motores editoriales. El navegador solo recibe estados, nunca claves recuperadas. Las peticiones requieren token y validan tamaño, tipo y proveedor; los cambios se serializan y los errores del llavero se presentan sin datos del secreto. Si no puede borrar una clave guardada, informa el fallo; no afirma haberla olvidado.
- Tres comprobaciones Rust aprobadas: handshake/orígenes, separación de proveedores y rechazo de peticiones de credenciales inválidas o sin autorización. Dos reinicios Linux verificaron recuperación y borrado de claves ficticias, rechazo de reemplazo inválido y ausencia de la clave en los archivos del perfil.
- WebKit se configura antes de cargar el documento. Permite captura de audio del origen local y deniega cámara/otros permisos. El audio virtual pasó AudioWorklet a 16 kHz, captura, transcripción Vosk, liberación de pistas y lectura eSpeak reproducida en WebKit. No se probó calidad de reconocimiento con una persona.
- **Límite confirmado en este equipo:** `RTCPeerConnection` no está expuesto en WebKitGTK 2.52.6 de Ubuntu 24.04, incluso activando el ajuste WebRTC y proporcionando plugins temporales de GStreamer. Por tanto OpenAI Realtime no funciona aquí mediante el transporte WebRTC actual. Se muestra un aviso antes de abrir el micrófono, sin fallback a otro proveedor. El soporte WebRTC depende también de cómo se compiló WebKit: [opciones de WebKitGTK 2.52.6](https://raw.githubusercontent.com/WebKit/WebKit/webkitgtk-2.52.6/Source/cmake/OptionsGTK.cmake). Agregar plugins por sí solo no resolvió este caso, por lo que no se añadieron dependencias innecesarias al instalador.
- La prueba informa WebRTC por separado; su ausencia no se presenta como una prueba WebRTC aprobada. Cuando está disponible intenta crear una oferta local sin servidores ICE ni proveedor remoto. No prueba una sesión OpenAI real.
- Gemini pasó en WebKit con transporte y token simulados: preparación, emisión de PCM, reproducción de PCM recibido y cierre de pistas. La ejecución final pasó sin `GST_PLUGIN_PATH` ni plugins temporales. Esto verifica el flujo de la interfaz y audio; no verifica autenticación, red, cuota ni una conversación real con Gemini.
- `tests/realtime_browser_check.py` pasó en Chromium con OpenAI simulado después del aviso de incompatibilidad. No se regeneraron los instaladores Electron 0.7.0 en este tramo; siguen siendo los artefactos de la entrega previa.
