# Motores editoriales

Codex con ChatGPT sigue siendo la integración principal. Los seis adaptadores alternativos son experimentales: tienen comprobaciones con respuestas simuladas, pero no validación contra cuentas reales. No equivalen al soporte de Codex.

En Configuración → Inteligencia artificial → Elegir motor editorial se elige el proveedor para el proyecto. El modelo se ingresa por su ID exacto; no hay catálogo ni selector de esfuerzo experimental. Se usa el razonamiento predeterminado del modelo. No hay cambio automático de proveedor ni reintento de pago.

| Motor | Transporte | Configuración |
| --- | --- | --- |
| Codex con ChatGPT | App Server, hilo persistente | Cuenta ChatGPT; catálogo y esfuerzos de la cuenta |
| OpenAI API | Responses, SSE, `store:false` | Clave OpenAI e ID de modelo |
| Google Gemini | Generate Content, SSE | Clave de AI Studio e ID sin prefijo `models/` |
| Anthropic | Messages, SSE | Clave Anthropic e ID de modelo |
| DeepSeek | Chat Completions, SSE | Clave DeepSeek e ID de modelo |
| Kimi | Chat Completions, SSE | Clave de Moonshot internacional e ID de modelo |
| Local | Chat Completions compatible, SSE | Servidor ya instalado, activo y modelo cargado; clave opcional |

El destino local admite HTTP de loopback con puerto y ruta `/v1`, por ejemplo `http://127.0.0.1:11434/v1` para Ollama o `http://127.0.0.1:1234/v1` para un servidor configurado en ese puerto. No descarga modelos ni administra ese servidor. La app solo conecta al equipo local; el usuario debe comprobar si el servidor/modelo elegido delega inferencia a la nube.

La voz tiene una elección separada. Sus claves no se reutilizan automáticamente para tareas editoriales. Ambos tipos pueden recordarse cifrados mediante el almacén nativo en escritorio; no se guardan claves en proyectos, exportaciones ni localStorage. Sin almacén seguro, solo memoria. Cambiar el motor no inicia una tarea; crear/retomar una entrevista o Enviar usa el elegido. Las APIs tienen condiciones y facturación propias.

## Contexto y control editorial

Todos reciben petición, idea, fuentes seleccionadas y decisiones. Los adaptadores reconstruyen el historial completado compatible con el objetivo y los hashes actuales; no incluyen turnos basados en fuentes retiradas o modificadas. Conservan un máximo explícito de 60.000 caracteres de historial sin recortarlo silenciosamente. Nueva conversación reinicia el contexto, conservando el registro local. Volver de un adaptador a Codex inicia un hilo con ese historial compatible.

Las guías integradas, propuestas, traducción y revisión humana siguen disponibles. Los adaptadores no reciben herramientas ni acceso al disco. Para propuestas y traducción se pide JSON y se valida localmente; si el modelo no lo cumple, falla la tarea sin aprobar ni modificar texto. Una salida interrumpida, filtrada o truncada no se marca completada. Se registra proveedor, modelo solicitado y modelo reportado cuando existe.

Límites experimentales: 8192 tokens de salida solicitados, 200.000 caracteres de respuesta, cuatro minutos comprobados entre lecturas y hasta 30 segundos de espera de red por lectura/conexión. Cancelar puede esperar ese intervalo si no llegan datos. Sin herramientas, catálogo automático, control de esfuerzo, imágenes ni evaluación de calidad por proveedor. Los modelos con requisitos distintos pueden rechazar la petición; se informa el error sin sustituirlos.

## Fuentes oficiales consultadas (2026-09-09)

- [OpenAI Responses](https://developers.openai.com/api/reference/cli/resources/responses/methods/create).
- [Gemini Generate Content](https://ai.google.dev/api/generate-content).
- [Anthropic streaming](https://platform.claude.com/docs/en/build-with-claude/streaming).
- [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/).
- [Kimi Chat Completions](https://platform.kimi.ai/docs/api/chat).
- [Compatibilidad OpenAI de Ollama](https://docs.ollama.com/api/openai-compatibility).

Pruebas: `python3 -m unittest discover -s tests`, `python3 tests/providers_browser_check.py` y `node tests/voice_vault_check.cjs`. Usan datos ficticios y transportes simulados; no consumen APIs.
