# Migración a Tauri — primer tramo

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
- Datos y perfil de la vista previa separados. El primer tramo ofrece claves en memoria e informa que no dispone todavía de persistencia segura. No intenta leer ni convertir los archivos cifrados de Electron.
- Se conservan ambos shells durante la transición. Antes de cambiar el producto distribuido faltan: almacén nativo y migración recuperable de preferencias/proyectos/claves, permisos y audio en Linux/Windows, cierre de tareas y descarga con diálogo nativo, instaladores Tauri y regresiones completas.

## Preparar y comprobar

Primero generar y verificar la build Electron del sistema nativo; luego:

```sh
python3 desktop/prepare_tauri.py
cargo test --manifest-path src-tauri/Cargo.toml
cargo build --manifest-path src-tauri/Cargo.toml
python3 tests/tauri_check.py
```

Rust y las dependencias de GTK pueden instalarse en una imagen aislada mediante `desktop/tauri-build.Dockerfile`. Montar únicamente `src-tauri`, `web` de solo lectura y un caché de Cargo; no montar proyectos ni credenciales. El helper prepara Linux o Windows x64 desde su propio sistema; no genera un sidecar Windows con el Python Linux.

La prueba de ventana usa un directorio temporal y ficción, sin cuenta ni micrófono. No prueba todo el producto ni autoriza declarar paridad con Electron. Los resultados observados se registran al completar la ejecución.

## Resultados observados — 2026-09-09

- Imagen aislada Rust 1.98.1/GTK de Debian; base fijada por digest y dependencias Rust fijadas en Cargo.lock. Compilación y prueba Rust de handshake/orígenes aprobadas.
- Sidecar Linux generado con PyInstaller y recursos verificados de Electron 0.7.0. Binario Tauri arrancado en este Linux con WebKitGTK del sistema, sin desactivar su sandbox.
- Dos arranques consecutivos sobre el mismo directorio temporal pasaron: proyecto ficticio, editor, navegación, tema recordado, 6 × 9 en libro 3D y descarga HTTP de DOCX. Sin sesión ChatGPT ni llamadas API.
- La primera comprobación de reinicio falló porque matar el lanzador no esperaba la liberación de Python. Se reemplazó por cierre de stdin y espera acotada de la salida del proceso. La repetición de ambos arranques pasó; el caso queda cubierto por `tests/tauri_check.py`.
- Aún no se validaron Tauri en Windows, audio ni almacén persistente. El DOCX se comprobó por HTTP; el diálogo de descarga/guardado del sistema sigue pendiente. La migración de datos/perfil/claves y los instaladores Tauri no están implementados en este tramo.
