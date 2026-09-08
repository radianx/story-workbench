# Prueba mínima de Codex App Server

Fecha: 2026-09-08. Ejecutada con `codex-cli 0.153.4`, Python 3.12 y cuenta ChatGPT administrada por Codex. Prototipo por stdio; no es un editor ni un servicio web.

## Repetir

```sh
python3 -m unittest discover -s scripts
python3 scripts/codex_smoke.py --live
```

Requiere Python 3.11+, `codex` instalado, login ChatGPT previo y build-novel disponible en la instalación local. `--live` consume cuota de la cuenta ChatGPT. App Server necesita acceder a su estado en CODEX_HOME (normalmente `~/.codex`) y conectarse al servicio. Dentro de otra sesión sandbox puede necesitar permiso de ejecución ampliado; el agente hijo conserva su sandbox de solo lectura.

El script exige cuenta de tipo `chatgpt` antes de crear cada sesión, fuerza ese método de autenticación y el proveedor OpenAI, elimina variables de API OpenAI del entorno hijo y rechaza una definición personalizada del proveedor. No inicia login, no lee tokens, no modifica la configuración global y no implementa fallback de pago. Desactiva los MCP y plugins declarados en la configuración del usuario, memorias, apps y subagentes para esta ejecución.

Solo crea un documento ficticio en una carpeta temporal. No recibe rutas de libros. Invoca build-novel mediante su ruta descubierta por `skills/list`, sin copiarla. El script muestra estados de comprobación, no texto de conversación, correo, tokens ni respuestas brutas del servidor. Codex conserva el hilo ficticio en su propio estado local; la carpeta temporal se elimina al terminar.

## Resultados observados

| Comprobación real | Resultado |
| --- | --- |
| Inicialización por stdio y `account/read` | Correcto; cuenta ChatGPT. |
| Descubrimiento e invocación explícita de build-novel | Correcto; skill local habilitada, turno completado. No demuestra toda su calidad editorial. |
| Creación de hilo con proveedor OpenAI y sandbox readOnly | Correcto. |
| Lectura y escritura mediante `command/exec` con readOnly | Leyó el documento; escritura de un archivo de prueba bloqueada con EROFS. |
| Streaming | Recibió deltas con la clave ficticia y el color leído. |
| Cancelación | Después de un delta, `turn/interrupt` produjo estado `interrupted`. |
| Reanudación | Cerró el proceso, abrió otro, reanudó el mismo hilo y recuperó clave y color sin repetirlos en la pregunta. |
| Integridad | Documento ficticio idéntico byte a byte; sin archivos adicionales en su carpeta. |
| Pruebas sin red | Cuatro pruebas unittest aprobadas: cuenta/configuración, eventos/errores, carrera de cancelación y rechazo de solicitudes de herramientas. |

Incidencias resueltas: el sandbox exterior impedía abrir el estado SQLite de Codex; fue necesaria ejecución ampliada. Cancelar inmediatamente después de `turn/start` devolvía `no active turn to interrupt`; ahora se espera actividad real. El bloqueo de escritura devuelve EROFS, además de los códigos de permisos habituales que contempla la comprobación.

## Límites y próximos pasos

- El caso de cuota agotada se comprobó con eventos sintéticos, no agotando la cuenta real. Tampoco se forzó caducidad de credenciales ni caída real de red.
- El sandbox de solo lectura bloquea escrituras, pero no restringe por sí solo las lecturas a la carpeta elegida. Esta prueba no accede a libros; el aislamiento de rutas, symlinks y cambios de proyecto sigue pendiente para el editor.
- Se rechazan solicitudes de aprobación de herramientas. No existe aún interfaz de aprobación editorial ni de permisos; son decisiones distintas.
- No se encontró LICENSE ni licencia declarada en el SKILL.md instalado de build-novel. Se usa localmente; derechos de redistribución sin resolver.
- Siguiente corte: editor local con texto ficticio, diagnóstico y propuesta separados, aceptación explícita y guardado con detección de conflictos. Sin ampliar todavía a libros privados, infraestructura o publicación.

Protocolo consultado en la [documentación oficial de App Server](https://learn.chatgpt.com/docs/app-server), contrastado con `codex app-server generate-json-schema` de la versión instalada. La [autenticación oficial](https://learn.chatgpt.com/docs/auth) distingue la cuenta ChatGPT del acceso con clave API.
